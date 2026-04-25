"""
Cross-Camera Matching Module — FAISS + Cosine Similarity.

Compares person embeddings across cameras to find matches.
Uses FAISS for fast approximate nearest-neighbor search.
Enforces temporal constraints to prevent stale matches.
"""

import time
import numpy as np
import faiss
from ai_pipeline.ai_config.config import Config


class CrossCameraMatcher:
    """
    FAISS-based cross-camera person matcher.

    Maintains a FAISS index of all known identity embeddings.
    When a new embedding arrives, queries the index for matches
    above the cosine similarity threshold within a temporal window.
    """

    def __init__(self):
        """Initialize the FAISS index and supporting structures."""
        self.embedding_dim = Config.REID_EMBEDDING_DIM
        self.temporal_window = Config.MATCH_TEMPORAL_WINDOW

        # Create a FAISS index for cosine similarity (inner product on L2-normed vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)

        # Metadata parallel to the FAISS index rows:
        # Each entry stores (global_id, camera_id, timestamp)
        self.index_metadata: list[dict] = []

        # GPU acceleration for FAISS if available
        if Config.FAISS_USE_GPU and faiss.get_num_gpus() > 0:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
            print("[Matcher] FAISS running on GPU")
        else:
            print("[Matcher] FAISS running on CPU")

        print(f"[Matcher] Thresholds(Same={Config.MATCH_THRESHOLD_SAME_CAM}/Diff={Config.MATCH_THRESHOLD_DIFF_CAM}), "
              f"TemporalWindow={self.temporal_window}s")

    def query(
        self,
        embedding: np.ndarray,
        camera_id: int,
        top_k: int = 5,
    ) -> tuple[int | None, float]:
        """
        Query the FAISS index to find the best matching global ID.

        Args:
            embedding: L2-normalized 512-D feature vector.
            camera_id: Camera where this detection comes from.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            (best_global_id, best_similarity) or (None, 0.0) if no match.
        """
        if self.index.ntotal == 0:
            return None, 0.0

        # Reshape for FAISS query (1, dim)
        query_vec = embedding.reshape(1, -1).astype(np.float32)

        # Search the index
        k = min(top_k, self.index.ntotal)
        similarities, indices = self.index.search(query_vec, k)

        current_time = time.time()
        best_global_id = None
        best_similarity = 0.0

        for sim, idx in zip(similarities[0], indices[0]):
            if idx < 0:
                continue

            meta = self.index_metadata[idx]

            # Temporal constraint: only match if the identity was seen recently
            time_diff = current_time - meta["timestamp"]
            if time_diff > self.temporal_window:
                continue

            # Adaptive thresholding: stricter for same-camera, looser for cross-camera
            threshold = Config.MATCH_THRESHOLD_SAME_CAM if meta["camera_id"] == camera_id else Config.MATCH_THRESHOLD_DIFF_CAM

            if sim > best_similarity and sim >= threshold:
                best_similarity = float(sim)
                best_global_id = meta["global_id"]

        return best_global_id, best_similarity

    def add_embedding(
        self,
        embedding: np.ndarray,
        global_id: int,
        camera_id: int,
    ):
        """
        Add an embedding to the FAISS index.

        Args:
            embedding: L2-normalized 512-D feature vector.
            global_id: The global identity ID.
            camera_id: Camera where the detection was made.
        """
        vec = embedding.reshape(1, -1).astype(np.float32)
        self.index.add(vec)
        self.index_metadata.append({
            "global_id": global_id,
            "camera_id": camera_id,
            "timestamp": time.time(),
        })

    def rebuild_index(self, identities: dict):
        """
        Rebuild the entire FAISS index from the global identity database.

        Called periodically to prune expired embeddings.

        Args:
            identities: Dict from global_id → identity_info dict containing
                        'embeddings', 'camera_id', 'last_seen'.
        """
        self.index.reset()
        self.index_metadata.clear()

        current_time = time.time()

        for gid, identity in identities.items():
            for emb_entry in identity.get("embedding_buffer", []):
                # Only index recent embeddings
                if current_time - emb_entry["timestamp"] < Config.IDENTITY_EXPIRY_TIME:
                    vec = emb_entry["embedding"].reshape(1, -1).astype(np.float32)
                    self.index.add(vec)
                    self.index_metadata.append({
                        "global_id": gid,
                        "camera_id": emb_entry.get("camera_id", -1),
                        "timestamp": emb_entry["timestamp"],
                    })

    def get_index_size(self) -> int:
        """Return the number of vectors in the FAISS index."""
        return self.index.ntotal
