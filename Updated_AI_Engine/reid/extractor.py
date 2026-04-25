"""
Person Re-Identification Module — OSNet (via torchreid).

Extracts 512-dimensional feature embeddings from person crops.
Handles preprocessing, batching, and GPU inference for speed.
"""

import numpy as np
import cv2
import torch
import torch.nn.functional as F
from torchvision import transforms
from config.config import Config

# torchreid for OSNet model
try:
    import torchreid
    TORCHREID_AVAILABLE = True
except ImportError:
    TORCHREID_AVAILABLE = False
    print("[ReID] WARNING: torchreid not installed. Install with: pip install torchreid")


class ReIDExtractor:
    """
    OSNet-based person re-identification feature extractor.

    Extracts normalized 512-D embeddings from person crop images.
    Supports single and batch extraction with GPU acceleration.
    """

    def __init__(self):
        """
        Initialize the OSNet model for feature extraction.
        Downloads pretrained weights automatically on first run.
        """
        self.device = Config.DEVICE
        self.input_size = Config.REID_INPUT_SIZE  # (H, W) = (256, 128)
        self.embedding_dim = Config.REID_EMBEDDING_DIM
        self.batch_size = Config.REID_BATCH_SIZE

        if TORCHREID_AVAILABLE:
            self._init_torchreid()
        else:
            self._init_fallback()

        # Preprocessing transform (ImageNet normalization)
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(self.input_size),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

        print(f"[ReID] OSNet loaded on {self.device}, "
              f"embedding dim={self.embedding_dim}")

    def _init_torchreid(self):
        """Initialize OSNet via torchreid library."""
        self.model = torchreid.models.build_model(
            name=Config.REID_MODEL_NAME,
            num_classes=1000,  # Not used for feature extraction
            pretrained=True,
        )
        self.model = self.model.to(self.device)
        self.model.eval()

    def _init_fallback(self):
        """
        Fallback: use torchvision's MobileNetV3 as a lightweight feature
        extractor when torchreid is not available. Produces 512-D embeddings
        via an added projection layer.
        """
        from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
        print("[ReID] Using MobileNetV3 fallback (torchreid not available)")

        backbone = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
        # Remove the classifier, keep the feature extractor
        backbone.classifier = torch.nn.Identity()
        self.model = backbone.to(self.device)
        self.model.eval()
        self.use_fallback_slice = True

    def crop_person(self, frame: np.ndarray, bbox: list[int]) -> np.ndarray | None:
        """
        Crop a person from the frame using a bounding box.

        Applies padding to handle edge cases and ensures minimum size.

        Args:
            frame: Full BGR frame.
            bbox: [x1, y1, x2, y2] bounding box.

        Returns:
            Cropped BGR image or None if the crop is too small.
        """
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox

        # Clamp to frame boundaries
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # Minimum crop size check
        crop_w = x2 - x1
        crop_h = y2 - y1
        if crop_w < 20 or crop_h < 40:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        return crop

    @torch.no_grad()
    def extract_single(self, crop: np.ndarray) -> np.ndarray | None:
        """
        Extract a feature embedding from a single person crop.

        Args:
            crop: BGR person crop image.

        Returns:
            L2-normalized embedding vector (512-D) or None on failure.
        """
        if crop is None or crop.size == 0:
            return None

        try:
            # Convert BGR → RGB for preprocessing
            rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            tensor = self.transform(rgb_crop).unsqueeze(0).to(self.device)

            # Forward pass
            features = self.model(tensor)
            if getattr(self, 'use_fallback_slice', False):
                features = features[:, :self.embedding_dim]

            # Mean-center to turn cosine similarity into Pearson correlation
            features = features - features.mean(dim=1, keepdim=True)

            # L2 normalize
            features = F.normalize(features, p=2, dim=1)

            return features.cpu().numpy().flatten()
        except Exception as e:
            print(f"[ReID] Extraction error: {e}")
            return None

    @torch.no_grad()
    def extract_batch(self, crops: list[np.ndarray]) -> list[np.ndarray | None]:
        """
        Extract feature embeddings from a batch of person crops.

        Args:
            crops: List of BGR person crop images.

        Returns:
            List of L2-normalized embedding vectors (512-D).
            Returns None for crops that failed preprocessing.
        """
        if not crops:
            return []

        # Preprocess all valid crops
        tensors = []
        valid_indices = []

        for i, crop in enumerate(crops):
            if crop is None or crop.size == 0:
                continue
            try:
                rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                tensor = self.transform(rgb_crop)
                tensors.append(tensor)
                valid_indices.append(i)
            except Exception:
                continue

        if not tensors:
            return [None] * len(crops)

        # Initialize results with None
        results = [None] * len(crops)

        # Process in batches
        for batch_start in range(0, len(tensors), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(tensors))
            batch = torch.stack(tensors[batch_start:batch_end]).to(self.device)

            features = self.model(batch)
            if getattr(self, 'use_fallback_slice', False):
                features = features[:, :self.embedding_dim]
            
            # Mean-center to turn cosine similarity into Pearson correlation
            features = features - features.mean(dim=1, keepdim=True)
            
            features = F.normalize(features, p=2, dim=1)
            features_np = features.cpu().numpy()

            for j, feat in enumerate(features_np):
                idx = valid_indices[batch_start + j]
                results[idx] = feat

        return results
