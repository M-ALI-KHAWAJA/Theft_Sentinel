"""
Central Configuration for Multi-Camera Theft Detection System.

Combines MCMT-ReID settings with X3D action classification settings.
"""

import torch
import os 
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Master configuration class."""

    # ──────────────────────────────────────────────
    # Device
    # ──────────────────────────────────────────────
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    # ──────────────────────────────────────────────
    # Camera / Input
    # ──────────────────────────────────────────────
    CAMERA_SOURCES = [
        "test_videos/cam1.mp4",
        "test_videos/cam2.mp4",
    ]
    CAMERA_IDS  = [1, 2]
    TARGET_FPS  = 15
    FRAME_WIDTH  = 1280    # resize frames before processing (was 640 — too small for 4K)
    FRAME_HEIGHT = 720

    # ──────────────────────────────────────────────
    # Detection (YOLOv8m — upgraded from yolov8n)
    # ──────────────────────────────────────────────
    YOLO_MODEL           = "yolov8m.pt"   # CHANGED: medium model, better accuracy
    YOLO_CONFIDENCE      = 0.45
    YOLO_IOU_THRESHOLD   = 0.5
    YOLO_PERSON_CLASS_ID = 0
    YOLO_IMG_SIZE        = 640

    # ──────────────────────────────────────────────
    # Tracking (DeepSORT)
    # ──────────────────────────────────────────────
    DEEPSORT_MAX_AGE            = 50
    DEEPSORT_N_INIT             = 3
    DEEPSORT_MAX_IOU_DISTANCE   = 0.7
    DEEPSORT_MAX_COSINE_DISTANCE = 0.3
    DEEPSORT_NN_BUDGET          = 100

    # ──────────────────────────────────────────────
    # ReID (OSNet)
    # ──────────────────────────────────────────────
    REID_MODEL_NAME   = "osnet_x1_0"
    REID_MODEL_WEIGHTS = "imagenet"
    REID_EMBEDDING_DIM = 512
    REID_INPUT_SIZE   = (256, 128)
    REID_BATCH_SIZE   = 32

    # ──────────────────────────────────────────────
    # Cross-Camera Matching
    # ──────────────────────────────────────────────
    MATCH_THRESHOLD_SAME_CAM = 0.70
    MATCH_THRESHOLD_DIFF_CAM = 0.40
    MATCH_TEMPORAL_WINDOW    = 30.0
    MATCH_MIN_EMBEDDINGS     = 3

    # ──────────────────────────────────────────────
    # Global Identity Database
    # ──────────────────────────────────────────────
    MAX_EMBEDDINGS_PER_IDENTITY = 50
    EMBEDDING_UPDATE_INTERVAL   = 5
    IDENTITY_EXPIRY_TIME        = 300.0

    # ──────────────────────────────────────────────
    # FAISS
    # ──────────────────────────────────────────────
    FAISS_USE_GPU = torch.cuda.is_available()
    FAISS_NPROBE  = 10

    # ──────────────────────────────────────────────
    # X3D Theft Classification  ← NEW
    # ──────────────────────────────────────────────
    X3D_MODEL_PATH = os.path.join(_BASE, "x3d_theft_model.pth")   # path to your trained .pth file
    X3D_CLIP_FRAMES    = 120   # frames to collect before inference (120 ≈ 4 sec @ 30fps)
    X3D_INFERENCE_EVERY = 30   # run X3D every N frames per person
    X3D_THEFT_THRESHOLD = 0.50 # probability above which we raise an alert
    X3D_SUSPICIOUS_THRESHOLD = 0.50  # show orange label above this

    # ──────────────────────────────────────────────
    # Visualization
    # ──────────────────────────────────────────────
    VIS_SHOW_LOCAL_ID   = True
    VIS_SHOW_GLOBAL_ID  = True
    VIS_BBOX_THICKNESS  = 2
    VIS_FONT_SCALE      = 0.6
    VIS_WINDOW_WIDTH    = 1280
    VIS_WINDOW_HEIGHT   = 720

    # ──────────────────────────────────────────────
    # Logging
    # ──────────────────────────────────────────────
    LOG_LEVEL      = "INFO"
    LOG_DETECTIONS = False
