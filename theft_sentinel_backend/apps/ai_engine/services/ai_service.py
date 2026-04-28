"""
AI Service — pipeline lifecycle manager (singleton).

Loads the new stack:
  • PersonDetector   (YOLOv8m)
  • ReIDExtractor    (OSNet via torchreid, MobileNetV3 fallback)
  • TheftClassifier  (X3D-S  —  x3d_theft_model.pth)
  • CrossCameraMatcher (FAISS inner-product index)
  • GlobalIdentityDatabase (in-memory, thread-safe internally)
  • ClipBuffer        (per-global-id rolling frame store)

Thread-safety contract
----------------------
inference_lock  — must be held around every GPU forward pass
                  (YOLO detect, OSNet extract_batch, X3D predict).
                  Prevents CUDA context contention when multiple
                  ContinuousMonitor threads run simultaneously.

state_lock      — must be held around every mutation of:
                    matcher (FAISS index), clip_buffer,
                    theft_scores, x3d_frame_counters.
                  GlobalIdentityDatabase manages its own internal
                  lock; callers do NOT need state_lock for db calls.

Both locks are exposed as attributes so InferenceRunner (and any
future consumer) share the exact same lock objects.

Public interface (unchanged from old service):
  AIService.get_instance()  → AIService singleton
  .initialize()             → bool
  .is_ready()               → bool
  .get_model_info()         → dict  (JSON-serialisable)
  .device                   → str
"""

import os
import threading
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ── model path constants (no sys.path manipulation — ai_pipeline/ is a normal
# package next to manage.py and has __init__.py in its root) ──────────────────
_BACKEND_DIR     = Path(__file__).resolve().parent.parent.parent.parent
_AI_PIPELINE_DIR = _BACKEND_DIR / "ai_pipeline"

# ── pipeline imports (fully-qualified — zero bare module names) ───────────────
from ai_pipeline.detection.detector   import PersonDetector
from ai_pipeline.reid.extractor       import ReIDExtractor
from ai_pipeline.x3d.classifier       import TheftClassifier, ClipBuffer
from ai_pipeline.matching.matcher     import CrossCameraMatcher
from ai_pipeline.database.identity_db import GlobalIdentityDatabase
from ai_pipeline.ai_config.config     import Config


class AIService:
    """
    Singleton service for the new AI pipeline.

    Usage
    -----
    service = AIService.get_instance()   # or AIService()
    service.initialize()                 # called once in apps.py ready()
    runner  = InferenceRunner()          # one per camera, shares service locks
    """

    _instance: Optional["AIService"] = None
    _class_lock = threading.Lock()
    _initialized: bool = False

    # ── singleton machinery ───────────────────────────────────────────────────

    def __new__(cls) -> "AIService":
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "AIService":
        return cls()

    def __init__(self) -> None:
        if self._initialized:
            return

        # ── pipeline models (populated by initialize()) ───────────────────
        self.detector:    Optional[PersonDetector]        = None
        self.reid:        Optional[ReIDExtractor]         = None
        self.x3d:         Optional[TheftClassifier]       = None
        self.matcher:     Optional[CrossCameraMatcher]    = None
        self.db:          Optional[GlobalIdentityDatabase] = None
        self.clip_buffer: Optional[ClipBuffer]            = None

        # ── shared per-global-id state (guarded by state_lock) ───────────
        # global_id → latest X3D theft probability (None = not yet scored)
        self.theft_scores:         Dict[int, Optional[float]] = {}
        # global_id → frame counter used to throttle X3D calls
        self.x3d_frame_counters:   Dict[int, int] = {}

        # ── thread-safety locks (exposed so InferenceRunner shares them) ──
        self.inference_lock = threading.Lock()   # GPU forward passes
        self.state_lock     = threading.Lock()   # FAISS / ClipBuffer / counters

        self.device: str = "cpu"

        # ── model paths from Django settings (with safe fallbacks) ────────
        try:
            from django.conf import settings
            self._yolo_weights = str(
                getattr(settings, "AI_PIPELINE_YOLO_WEIGHTS",
                        _AI_PIPELINE_DIR / "yolov8m.pt")
            )
            self._x3d_weights = str(
                getattr(settings, "AI_PIPELINE_X3D_WEIGHTS",
                        _AI_PIPELINE_DIR / "x3d_theft_model.pth")
            )
        except Exception:
            self._yolo_weights = str(_AI_PIPELINE_DIR / "yolov8m.pt")
            self._x3d_weights  = str(_AI_PIPELINE_DIR / "x3d_theft_model.pth")

        AIService._initialized = True

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """
        Load all pipeline models.  Called once by apps.AiEngineConfig.ready().
        """
        try:
            logger.info("🚀 Initialising AI Service (YOLOv8m + OSNet + X3D) …")

            # ── Device ────────────────────────────────────────────────────
            if torch.cuda.is_available():
                self.device = "cuda:0"
                torch.backends.cudnn.benchmark = True
                logger.info(f"✅ CUDA: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.warning("⚠️  CUDA not available — using CPU (slower)")

            # Override Config class-attributes so every pipeline module
            # sees the same device and model paths.
            Config.DEVICE         = self.device.split(":")[0]   # "cuda" | "cpu"
            Config.YOLO_MODEL     = self._yolo_weights
            Config.X3D_MODEL_PATH = self._x3d_weights

            # ── YOLOv8m detector ──────────────────────────────────────────
            logger.info(f"📦 Loading YOLOv8m detector: {self._yolo_weights}")
            self.detector = PersonDetector()
            logger.info("✅ Detector loaded")

            # ── OSNet ReID extractor ──────────────────────────────────────
            logger.info("📦 Loading OSNet ReID extractor …")
            self.reid = ReIDExtractor()
            logger.info("✅ ReID extractor loaded")

            # ── X3D-S classifier ──────────────────────────────────────────
            logger.info(f"📦 Loading X3D classifier: {self._x3d_weights}")
            self.x3d = TheftClassifier(self._x3d_weights, Config.DEVICE)
            logger.info("✅ X3D classifier loaded")

            # ── FAISS matcher ─────────────────────────────────────────────
            logger.info("📦 Initialising FAISS cross-camera matcher …")
            self.matcher = CrossCameraMatcher()
            logger.info("✅ Matcher initialised")

            # ── Global identity DB (pure in-memory) ───────────────────────
            logger.info("📦 Initialising GlobalIdentityDatabase …")
            self.db = GlobalIdentityDatabase()
            logger.info("✅ Identity DB initialised")

            # ── ClipBuffer (per-global-id X3D frame store) ────────────────
            self.clip_buffer = ClipBuffer(max_frames=Config.X3D_CLIP_FRAMES)
            logger.info(
                f"✅ ClipBuffer ready "
                f"(max_frames={Config.X3D_CLIP_FRAMES}, "
                f"sampled={Config.X3D_CLIP_FRAMES} → 180 uniform)"
            )

            # ── YOLO warmup ───────────────────────────────────────────────
            logger.info("🔥 Warming up YOLO …")
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.detector.detect(dummy)
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            logger.info("✅ Warmup complete")

            logger.info("✅ AI Service ready (new pipeline)")
            return True

        except Exception as exc:
            logger.error(f"❌ AI Service init failed: {exc}", exc_info=True)
            raise

    # ── public API (unchanged shapes) ─────────────────────────────────────────

    def is_ready(self) -> bool:
        """Return True when all six pipeline components are loaded."""
        return (
            self.detector    is not None
            and self.reid        is not None
            and self.x3d         is not None
            and self.matcher     is not None
            and self.db          is not None
            and self.clip_buffer is not None
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict describing loaded models."""
        return {
            "detection_model":       self._yolo_weights,
            "reid_model":            f"OSNet ({Config.REID_MODEL_NAME})",
            "x3d_model":             self._x3d_weights,
            "x3d_clip_frames":       Config.X3D_CLIP_FRAMES,
            "x3d_theft_threshold":   Config.X3D_THEFT_THRESHOLD,
            "x3d_suspicious_threshold": Config.X3D_SUSPICIOUS_THRESHOLD,
            "device":                self.device,
            "cuda_available":        torch.cuda.is_available(),
            "models_loaded":         self.is_ready(),
        }

    # ── maintenance helpers (called from InferenceRunner) ─────────────────────

    def prune_expired_identities(self) -> None:
        """Prune expired global IDs from DB, ClipBuffer, and counter dicts."""
        # CRITICAL: Identity memory must be permanent.
        # DO NOT purge or delete global_ids from FAISS or the central database.
        pass

    def rebuild_matcher_index(self) -> None:
        """Rebuild the FAISS index from current identity DB embeddings."""
        identities = self.db.get_all_identities()
        identity_data = {
            gid: {"embedding_buffer": list(rec.embedding_buffer)}
            for gid, rec in identities.items()
        }
        with self.state_lock:
            self.matcher.rebuild_index(identity_data)


# ── global suspect registry methods ───────────────────────────────────────────

    def add_active_thief(self, global_id: int) -> None:
        with self.state_lock:
            gid_str = str(global_id)
            thieves = cache.get('active_thief_global_ids', [])
            thieves = [str(x) for x in thieves]
            if gid_str not in thieves:
                thieves.append(gid_str)
                cache.set('active_thief_global_ids', thieves, timeout=None)
            
    def remove_active_thief(self, global_id: int) -> None:
        with self.state_lock:
            gid_str = str(global_id)
            thieves = cache.get('active_thief_global_ids', [])
            thieves = [str(x) for x in thieves]
            if gid_str in thieves:
                thieves.remove(gid_str)
                cache.set('active_thief_global_ids', thieves, timeout=None)
            
    def is_active_thief(self, global_id: int) -> bool:
        if global_id is None: return False
        gid_str = str(global_id)
        thieves = cache.get('active_thief_global_ids', [])
        return gid_str in [str(x) for x in thieves]


# ── module-level singleton ────────────────────────────────────────────────────
ai_service = AIService()
