# dedup/core/hasher.py

import hashlib
from dataclasses import dataclass

from dedup.config.settings import (
    HASH_ALGO,
    BLAKE_AVAILABLE,
    HASH_CHUNK_SIZE,
    PARTIAL_HASH_BYTES,
)

if BLAKE_AVAILABLE:
    import blake3


@dataclass
class HashResult:
    full_hash: str
    partial_hash: str
    algo: str


class Hasher:
    """
    Streaming hasher supporting blake3 (preferred) or SHA256 fallback.
    Produces both partial and full hashes for fast dedup workflows.
    """

    def __init__(self):
        self.algo = HASH_ALGO.lower()

    def _new_hasher(self):
        if self.algo == "blake3" and BLAKE_AVAILABLE:
            return blake3.blake3()
        return hashlib.sha256()

    def hash_file(self, path: str) -> HashResult:
        """
        Compute partial + full hash for a file using streaming reads.
        """

        full_hasher = self._new_hasher()
        partial_hasher = self._new_hasher()

        bytes_remaining = PARTIAL_HASH_BYTES

        with open(path, "rb") as f:
            while True:
                chunk = f.read(HASH_CHUNK_SIZE)
                if not chunk:
                    break

                # Full hash always updates
                full_hasher.update(chunk)

                # Partial hash only updates until limit reached
                if bytes_remaining > 0:
                    part = chunk[:bytes_remaining]
                    partial_hasher.update(part)
                    bytes_remaining -= len(part)

        full_hex = (
            full_hasher.hexdigest()
            if self.algo != "blake3"
            else full_hasher.hexdigest()
        )

        partial_hex = (
            partial_hasher.hexdigest()
            if self.algo != "blake3"
            else partial_hasher.hexdigest()
        )

        return HashResult(
            full_hash=full_hex,
            partial_hash=partial_hex,
            algo=self.algo,
        )
