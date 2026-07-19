# dedup/pipeline/parallel_ingest.py

import queue
import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from dedup.config.settings import SCAN_ROOTS, DB_BACKEND, DB_PG_URL, DB_SQLITE_PATH
from dedup.core.scanner import Scanner
from dedup.core.hasher import Hasher
from dedup.db.loader import SQLLoader
from dedup.db.postgres import PostgresDB
from dedup.db.sqlite import SQLiteDB
from dedup.similarity.multimodal_similarity_engine import (
    MultimodalSimilarityEngine as engine,
)
from similarity.extractors.phash_extractor import extract_phash
from similarity.extractors.orb_extractor import extract_orb_descriptor
from similarity.extractors.clip_extractor import extract_clip_embedding


def get_db():
    loader = SQLLoader(DB_BACKEND)
    if DB_BACKEND == "postgres":
        return PostgresDB(loader, DB_PG_URL)
    return SQLiteDB(loader, str(DB_SQLITE_PATH))


def insert_record(db, info, hashes):
    """
    Existing DB insert, now extended to include pHash, ORB, and CLIP.
    Your SQLLoader already maps 'insert_file' to the correct SQL.
    """
    db.execute(
        "insert_file",
        info.path,
        info.filename,
        info.filename_no_ext,
        info.extension,
        info.parent_folder,
        info.object_type,
        hashes.full_hash,
        info.size,
        info.created_at,
        info.modified_at,
        info.scanned_at,
        # --- NEW fields ---
        hashes.phash,
        hashes.orb_descriptor,
        hashes.clip_embedding,
    )


def run_parallel_ingestion(max_workers: int = 8):
    """
    Parallel scan + hash + extractor + DB ingest using bounded queues.
    """

    if not SCAN_ROOTS:
        print(
            "[parallel_ingest] No scan roots defined. Check DEDUP_SCAN_ROOT_* in .env"
        )
        return

    db = get_db()
    db.execute("create_tables")

    scan_queue: queue.Queue = queue.Queue(maxsize=1000)
    db_queue: queue.Queue = queue.Queue(maxsize=1000)

    scanner = Scanner(SCAN_ROOTS)
    hasher = Hasher()

    # --- Scanner thread ---
    def scan_worker():
        for info in scanner.scan():
            scan_queue.put(info)
        scan_queue.put(None)  # poison pill

    # --- Hash + Extractor workers ---
    def hash_worker(info):
        # 1. Full-file hash (your existing logic)
        hashes = hasher.hash_file(info.path)

        # 2. Run extractors
        # 2.1 Image extractors (pHash, ORB, CLIP)
        if info.object_type == "image":
            try:
                hashes.phash = extract_phash(info.path)
            except Exception as e:
                print(f"[extractor] pHash failed for {info.path}: {e}")
                hashes.phash = b"\x00" * 8

            try:
                hashes.orb_descriptor = extract_orb_descriptor(info.path)
            except Exception as e:
                print(f"[extractor] ORB failed for {info.path}: {e}")
                hashes.orb_descriptor = b"\x00" * 32

            try:
                hashes.clip_embedding = extract_clip_embedding(info.path)
            except Exception as e:
                print(f"[extractor] CLIP failed for {info.path}: {e}")
                hashes.clip_embedding = b"\x00" * (512 * 4)  # float32 * 512

        # ToDo: audio, video, documents, etc.
        # 2.2 Audio extractors ...
        # if info.object_type == "audio":
        #     pass
        # 2.3 Video extractors ...
        # if info.object_type == "video":
        #     pass
        # 2.4 Document extractors ...
        # if info.object_type == "document":
        #     pass

        # 3. Push to DB queue
        db_queue.put((info, hashes))

    # --- DB writer thread ---
    def db_worker():
        processed = 0
        while True:
            item = db_queue.get()
            if item is None:
                break
            info, hashes = item
            insert_record(db, info, hashes)
            processed += 1

        if info.object_type == "image":
            # Convert raw bytes to numpy vectors
            phash_bits = np.frombuffer(hashes.phash, dtype=np.uint8)
            orb_vector = np.frombuffer(hashes.orb_descriptor, dtype=np.uint8)
            clip_vector = np.frombuffer(hashes.clip_embedding, dtype=np.float32)

            # Skip zero vectors (corrupted or unreadable images)
            if not (phash_bits.any() or orb_vector.any() or clip_vector.any()):
                pass  # do not index zero vectors
            else:
                engine.add_image(
                    file_id=db.last_insert_id(),
                    phash_bits=phash_bits,
                    orb_vector=orb_vector,
                    clip_vector=clip_vector,
                )
            if processed % 1000 == 0:
                print(f"[parallel_ingest] DB: {processed} files ingested...")

        print(f"[parallel_ingest] Completed. Total files ingested: {processed}")

    # Start scanner + DB writer
    threading.Thread(target=scan_worker, daemon=True).start()
    threading.Thread(target=db_worker, daemon=True).start()

    # Hash worker pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            info = scan_queue.get()
            if info is None:
                break
            executor.submit(hash_worker, info)

    # Signal DB writer to stop
    db_queue.put(None)
