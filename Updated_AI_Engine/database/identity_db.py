"""
Global Identity Database Module.

Maintains a centralized database of all known person identities.
Each identity stores:
    - Global ID (unique)
    - Rolling buffer of recent embeddings (Multi-Embedding Buffer)
    - Camera-wise tracking history
    - Timestamps for temporal constraint enforcement

Thread-safe for concurrent multi-camera updates.
"""

import time
import threading
import numpy as np
from collections import deque
from config.config import Config


class IdentityRecord:
    """
    Represents a single globally tracked person identity.

    Maintains a rolling buffer of the last N embeddings for robust matching.
    """

    def __init__(self, global_id: int, embedding: np.ndarray, camera_id: int):
        self.global_id = global_id
        self.created_at = time.time()
        self.last_seen = time.time()

        # Multi-Embedding Buffer: stores recent embeddings for robust matching
        self.embedding_buffer: deque = deque(
            maxlen=Config.MAX_EMBEDDINGS_PER_IDENTITY
        )
        self.embedding_buffer.append({
            "embedding": embedding,
            "camera_id": camera_id,
            "timestamp": time.time(),
        })

        # Average embedding (updated on each new addition)
        self._avg_embedding = embedding.copy()

        # Camera-wise tracking history: {camera_id: [(track_id, timestamp), ...]}
        self.camera_history: dict[int, list[tuple]] = {}
        self.update_camera_history(camera_id, -1)  # -1 = initial assignment

        # Statistics
        self.total_sightings = 1
        self.cameras_seen: set[int] = {camera_id}

    def add_embedding(self, embedding: np.ndarray, camera_id: int):
        """
        Add a new embedding to the rolling buffer and update the average.

        Args:
            embedding: L2-normalized 512-D vector.
            camera_id: Camera where this was observed.
        """
        self.embedding_buffer.append({
            "embedding": embedding,
            "camera_id": camera_id,
            "timestamp": time.time(),
        })
        self.last_seen = time.time()
        self.total_sightings += 1
        self.cameras_seen.add(camera_id)

        # Recompute average embedding
        all_embs = [e["embedding"] for e in self.embedding_buffer]
        self._avg_embedding = np.mean(all_embs, axis=0)
        # Re-normalize
        norm = np.linalg.norm(self._avg_embedding)
        if norm > 0:
            self._avg_embedding /= norm

    def get_average_embedding(self) -> np.ndarray:
        """Return the average of all buffered embeddings (L2-normalized)."""
        return self._avg_embedding

    def get_best_match_score(self, query_embedding: np.ndarray) -> float:
        """
        Compute the best cosine similarity between the query and all buffered
        embeddings. This is more robust than using only the average.

        Args:
            query_embedding: L2-normalized 512-D vector.

        Returns:
            Max cosine similarity score.
        """
        best_score = 0.0
        for entry in self.embedding_buffer:
            score = float(np.dot(query_embedding, entry["embedding"]))
            if score > best_score:
                best_score = score
        return best_score

    def update_camera_history(self, camera_id: int, track_id: int):
        """Record that this identity was seen in a specific camera."""
        if camera_id not in self.camera_history:
            self.camera_history[camera_id] = []
        self.camera_history[camera_id].append((track_id, time.time()))

    def is_expired(self) -> bool:
        """Check if this identity has expired (not seen for too long)."""
        return (time.time() - self.last_seen) > Config.IDENTITY_EXPIRY_TIME

    def to_dict(self) -> dict:
        """Serialize to dict for output/logging."""
        return {
            "global_id": self.global_id,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "total_sightings": self.total_sightings,
            "cameras_seen": list(self.cameras_seen),
            "embedding_count": len(self.embedding_buffer),
        }


class GlobalIdentityDatabase:
    """
    Thread-safe global identity database.

    Provides methods to:
        - Register new identities
        - Match query embeddings against all known identities
        - Update existing identities with new embeddings
        - Prune expired identities
    """

    def __init__(self):
        """Initialize the database."""
        self._lock = threading.Lock()
        self._identities: dict[int, IdentityRecord] = {}
        self._next_global_id = 1

        # Mapping: (camera_id, track_id) → global_id for fast lookup
        self._track_to_global: dict[tuple[int, int], int] = {}

        print("[IdentityDB] Global identity database initialized")

    def register_new_identity(
        self,
        embedding: np.ndarray,
        camera_id: int,
        track_id: int,
    ) -> int:
        """
        Create a new global identity.

        Args:
            embedding: L2-normalized 512-D feature vector.
            camera_id: Camera ID where the person was first seen.
            track_id: Local track ID in that camera.

        Returns:
            The newly assigned global ID.
        """
        with self._lock:
            gid = self._next_global_id
            self._next_global_id += 1

            self._identities[gid] = IdentityRecord(gid, embedding, camera_id)
            self._track_to_global[(camera_id, track_id)] = gid

            return gid

    def update_identity(
        self,
        global_id: int,
        embedding: np.ndarray,
        camera_id: int,
        track_id: int,
    ):
        """
        Update an existing identity with a new embedding.

        Args:
            global_id: The global ID to update.
            embedding: New L2-normalized embedding.
            camera_id: Camera where observed.
            track_id: Local track ID.
        """
        with self._lock:
            if global_id in self._identities:
                record = self._identities[global_id]
                record.add_embedding(embedding, camera_id)
                record.update_camera_history(camera_id, track_id)
                self._track_to_global[(camera_id, track_id)] = global_id

    def find_match(
        self,
        embedding: np.ndarray,
        camera_id: int,
        exclude_global_id: int | None = None,
    ) -> tuple[int | None, float]:
        """
        Find the best matching identity for an embedding using
        direct comparison against all identity records.

        This is the fallback/complement to FAISS matching.
        Uses both average and best-match strategies for robustness.

        Args:
            embedding: L2-normalized query embedding.
            camera_id: Camera where the detection occurred.
            exclude_global_id: Skip this ID (e.g., to avoid self-matching).

        Returns:
            (best_global_id, best_score) or (None, 0.0).
        """
        with self._lock:
            best_gid = None
            best_score = 0.0
            current_time = time.time()

            for gid, record in self._identities.items():
                if gid == exclude_global_id:
                    continue

                # Temporal constraint
                time_since_last = current_time - record.last_seen
                if time_since_last > Config.MATCH_TEMPORAL_WINDOW:
                    continue

                # Use best-match-in-buffer strategy (most robust)
                score = record.get_best_match_score(embedding)

                # Adaptive threshold based on history
                threshold = Config.MATCH_THRESHOLD_SAME_CAM if camera_id in record.cameras_seen else Config.MATCH_THRESHOLD_DIFF_CAM

                if score > best_score and score >= threshold:
                    best_score = score
                    best_gid = gid

            return best_gid, best_score

    def get_global_id_for_track(self, camera_id: int, track_id: int) -> int | None:
        """
        Look up the global ID assigned to a (camera_id, track_id) pair.

        Returns:
            Global ID or None if not yet assigned.
        """
        with self._lock:
            return self._track_to_global.get((camera_id, track_id))

    def get_identity(self, global_id: int) -> IdentityRecord | None:
        """Get an identity record by global ID."""
        with self._lock:
            return self._identities.get(global_id)

    def get_all_identities(self) -> dict[int, IdentityRecord]:
        """Return a copy of all identity records."""
        with self._lock:
            return dict(self._identities)

    def prune_expired(self) -> int:
        """
        Remove expired identities from the database.

        Returns:
            Number of identities removed.
        """
        with self._lock:
            expired_ids = [
                gid for gid, record in self._identities.items()
                if record.is_expired()
            ]

            for gid in expired_ids:
                del self._identities[gid]
                # Clean up track mapping
                keys_to_remove = [
                    k for k, v in self._track_to_global.items() if v == gid
                ]
                for k in keys_to_remove:
                    del self._track_to_global[k]

            if expired_ids:
                print(f"[IdentityDB] Pruned {len(expired_ids)} expired identities")

            return len(expired_ids)

    def get_stats(self) -> dict:
        """Return database statistics."""
        with self._lock:
            return {
                "total_identities": len(self._identities),
                "active_tracks": len(self._track_to_global),
                "next_global_id": self._next_global_id,
            }
