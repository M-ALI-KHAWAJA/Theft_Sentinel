"""
X3D Theft Classifier Module.

Contains:
  - ClipBuffer: stores per-person video frames, produces tensors for X3D
  - TheftClassifier: loads trained X3D-S model, runs inference

Taken from x3d_allModels.py and adapted for multi-camera use.
Person clips are now keyed by GLOBAL ID (not local track ID) so the
same person is tracked correctly across cameras.
"""

import cv2
import torch
import torch.nn as nn
import numpy as np
from collections import deque, defaultdict
from typing import Optional


# ─── X3D input configuration ─────────────────────────────────────────────────
CLIP_SIZE      = (224, 224)   # spatial size expected by X3D
SAMPLED_FRAMES = 180          # temporal size expected by X3D-S
# ─────────────────────────────────────────────────────────────────────────────


class ClipBuffer:
    """
    Per-person rolling frame buffer.

    Keyed by global_id so the same person maps to one buffer even when
    seen across multiple cameras.

    Stores raw BGR crops resized to (224, 224).
    When the buffer is full it returns a normalized tensor ready for X3D.
    """

    def __init__(self, max_frames: int = 120):
        """
        Args:
            max_frames: How many frames to collect before inference is
                        possible. 120 frames ≈ 4 seconds at 30 fps.
        """
        self.max_frames = max_frames
        # global_id (int) → deque of (224,224,3) uint8 arrays
        self.buffers: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=max_frames)
        )
        self.last_seen_time: dict[int, float] = {}

    # ── public API ────────────────────────────────────────────────────────────

    def add_frame(self, global_id: int, person_crop: np.ndarray):
        """
        Resize and store one frame for a person.

        Args:
            global_id: Cross-camera global identity ID.
            person_crop: BGR image of the person (any size).
        """
        if person_crop is None or getattr(person_crop, "size", 0) == 0:
            return
        resized = cv2.resize(person_crop, CLIP_SIZE)
        self.buffers[global_id].append(resized)
        
        import time
        self.last_seen_time[global_id] = time.time()

    def get_clip(self, global_id: int) -> Optional[torch.Tensor]:
        """
        Build a normalised tensor from the buffer when enough frames exist.

        Uses uniform temporal sampling so the temporal density matches
        training (critical — mismatch caused near-zero accuracy in the
        original deployment).

        Returns:
            Tensor [1, 3, 180, 224, 224] on CPU, or None if not ready.
        """
        frames = list(self.buffers.get(global_id, []))
        if len(frames) < self.max_frames:
            return None

        # Uniform temporal subsampling to exactly SAMPLED_FRAMES
        indices = np.linspace(0, len(frames) - 1, SAMPLED_FRAMES).astype(int)
        sampled = [frames[i] for i in indices]

        # [T, H, W, C] → [C, T, H, W]
        clip = np.array(sampled, dtype=np.float32)          # [180,224,224,3]
        clip = torch.from_numpy(clip).permute(3, 0, 1, 2)   # [3,180,224,224]

        # Normalize (video mean/std from Kinetics-400)
        clip = clip / 255.0
        mean = torch.tensor([0.45, 0.45, 0.45]).view(3, 1, 1, 1)
        std  = torch.tensor([0.225, 0.225, 0.225]).view(3, 1, 1, 1)
        clip = (clip - mean) / std

        return clip.unsqueeze(0)   # [1,3,180,224,224]

    def buffer_size(self, global_id: int) -> int:
        """How many frames are currently stored for this person."""
        return len(self.buffers.get(global_id, []))

    def remove_person(self, global_id: int):
        """Free memory when a global identity expires."""
        self.buffers.pop(global_id, None)
        self.last_seen_time.pop(global_id, None)

    def cleanup_stale_buffers(self):
        """
        Explicitly free RAM for people who walked off-screen (> 2 seconds ago),
        unless the system is actively encoding a theft clip.
        """
        import time
        import threading
        
        # CRITICAL SAFETY GUARD: Do not delete buffers if an alert clip is encoding
        is_encoding = any(t.name.startswith("clip-upload-") for t in threading.enumerate())
        if is_encoding:
            return
            
        now = time.time()
        stale_ids = [gid for gid, last in self.last_seen_time.items() if now - last > 2.0]
        for gid in stale_ids:
            if gid in self.buffers:
                del self.buffers[gid]
            if gid in self.last_seen_time:
                del self.last_seen_time[gid]


# ─────────────────────────────────────────────────────────────────────────────


class TheftClassifier:
    """
    Wrapper around the trained X3D-S model.

    Loads weights from a checkpoint produced by the training script.
    Falls back to random predictions (demo mode) if the file is missing.
    """

    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model = None

        print(f"[X3D] Loading model from {model_path} ...")
        try:
            # ── Build architecture (must match training) ──────────────────
            model = torch.hub.load(
                "facebookresearch/pytorchvideo",
                "x3d_s",
                pretrained=False,
                verbose=False,
            )

            # Replace final projection with 2-class head
            if hasattr(model, "blocks"):
                in_features = model.blocks[5].proj.in_features
                model.blocks[5].proj = nn.Linear(in_features, 2)
            elif hasattr(model, "head") and hasattr(model.head, "proj"):
                in_features = model.head.proj.in_features
                model.head.proj = nn.Linear(in_features, 2)

            # ── Load weights ──────────────────────────────────────────────
            checkpoint = torch.load(
                model_path,
                map_location=self.device,
                weights_only=False,   # needed for numpy scalars in checkpoint
            )
            model.load_state_dict(checkpoint["model_state_dict"])
            model.to(self.device)
            model.eval()
            self.model = model

            acc   = checkpoint.get("accuracy", 0)
            epoch = checkpoint.get("epoch", 0)
            print(f"[X3D] ✓ Loaded — accuracy: {acc:.2%}, epochs: {epoch + 1}")

        except FileNotFoundError:
            print(f"[X3D] ⚠ Model file not found: {model_path}")
            print("[X3D] ⚠ Running in DEMO mode (random predictions)")
        except Exception as exc:
            print(f"[X3D] ⚠ Load error: {exc}")
            print("[X3D] ⚠ Running in DEMO mode (random predictions)")

    # ── inference ─────────────────────────────────────────────────────────────

    def predict(self, clip: torch.Tensor) -> float:
        """
        Run inference on a clip tensor.

        Args:
            clip: Tensor [1, 3, 180, 224, 224]

        Returns:
            Theft probability in [0, 1].
        """
        if self.model is None:
            return float(np.random.random())   # demo mode

        with torch.no_grad():
            clip = clip.to(self.device)
            logits = self.model(clip)              # [1, 2]
            probs  = torch.softmax(logits, dim=1)
            return float(probs[0, 1].item())       # class-1 = theft
