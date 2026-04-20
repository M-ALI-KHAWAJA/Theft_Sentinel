"""
AI Service
Manages the AI pipeline lifecycle (loading models, initialization)
"""
import os
import sys
import torch
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Add ModelExport to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_EXPORT_PATH = BASE_DIR / "ModelExport"
sys.path.insert(0, str(MODEL_EXPORT_PATH))

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from ml_classifier.theft_classifier import TheftClassifier


class AIService:
    """
    Singleton service to manage AI models
    DO NOT MODIFY MODELEXPORT - ONLY WRAP IT
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.det_model = None
            self.pose_model = None
            self.deepsort = None
            self.ml_classifier = None
            self.device = "cpu"
            
            # Model paths (YOUR EXACT STRUCTURE)
            self.det_model_path = MODEL_EXPORT_PATH / "yolov8l.pt"
            self.pose_model_path = MODEL_EXPORT_PATH / "yolov8l-pose.pt"
            self.ml_model_path = MODEL_EXPORT_PATH / "trained_models" / "theft_classifier.pkl"
            
            AIService._initialized = True
    
    def initialize(self):
        """
        Initialize all AI models
        This is called once at startup
        """
        try:
            logger.info("🚀 Initializing AI Service...")
            
            # Check CUDA availability
            if torch.cuda.is_available():
                self.device = "cuda:0"
                torch.backends.cudnn.benchmark = True
                logger.info(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                logger.warning("⚠️ CUDA not available. Using CPU (slower)")
            
            # Load Detection Model
            logger.info(f"📦 Loading detection model: {self.det_model_path}")
            if not self.det_model_path.exists():
                raise FileNotFoundError(f"Detection model not found: {self.det_model_path}")
            
            self.det_model = YOLO(str(self.det_model_path))
            self.det_model.to(self.device)
            logger.info("✅ Detection model loaded")
            
            # Load Pose Model
            logger.info(f"📦 Loading pose model: {self.pose_model_path}")
            if not self.pose_model_path.exists():
                raise FileNotFoundError(f"Pose model not found: {self.pose_model_path}")
            
            self.pose_model = YOLO(str(self.pose_model_path))
            self.pose_model.to(self.device)
            logger.info("✅ Pose model loaded")
            
            # Initialize DeepSORT
            logger.info("📦 Initializing DeepSORT tracker...")
            embedder_gpu = self.device.startswith("cuda")
            self.deepsort = DeepSort(
                max_age=25,
                n_init=3,
                max_iou_distance=0.7,
                max_cosine_distance=0.4,
                nn_budget=100,
                embedder="mobilenet",
                embedder_gpu=embedder_gpu,
            )
            logger.info("✅ DeepSORT initialized")
            
            # Load ML Classifier
            logger.info(f"📦 Loading ML classifier: {self.ml_model_path}")
            self.ml_classifier = TheftClassifier(str(self.ml_model_path))
            if self.ml_classifier.model is not None:
                logger.info("✅ ML classifier loaded")
            else:
                logger.warning("⚠️ ML classifier not loaded (file may not exist)")
            
            # Warmup models
            logger.info("🔥 Warming up models...")
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            self.det_model(dummy_frame, imgsz=640, conf=0.5, verbose=False)
            self.pose_model(dummy_frame, imgsz=320, conf=0.3, verbose=False)
            if self.device.startswith("cuda"):
                torch.cuda.synchronize()
            logger.info("✅ Warmup complete")
            
            logger.info("✅ AI Service initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Service: {str(e)}")
            raise
    
    def is_ready(self) -> bool:
        """Check if all models are loaded"""
        return (
            self.det_model is not None and
            self.pose_model is not None and
            self.deepsort is not None
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "detection_model": str(self.det_model_path),
            "pose_model": str(self.pose_model_path),
            "ml_classifier": str(self.ml_model_path),
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "models_loaded": self.is_ready(),
            "ml_classifier_loaded": self.ml_classifier is not None and self.ml_classifier.model is not None
        }


# Singleton instance
ai_service = AIService()

