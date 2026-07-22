# tests/test_db_basic.py

from dedup.pipeline.parallel_ingest import get_db
from dedup.tests.utils.db_reset import reset_files_table


def pretty_row(row):
    file_id, clip = row

    # Convert memoryview → bytes
    if isinstance(clip, memoryview):
        clip = clip.tobytes()

    # Show a readable summary
    return {
        "file_id": file_id,
        "clip_embedding_len": len(clip),
        "clip_embedding_preview": clip[:16].hex(),  # first 16 bytes
    }


def test_db_basic():
    """
    Basic DB sanity test:
    - create tables
    - insert one image row
    - query via select_all_images_with_clip
    """

    print(f"[DEBUG] ({__file__})  In {__name__} running test_db_basic()...")
    db = get_db()
    print(f"[DEBUG] ({__file__})  DB connection: {db}")

    # Clean slate (test-only)
    reset_files_table(db)
    print(f"[DEBUG] ({__file__})  Files table reset")

    # Insert a dummy image row
    file_id = db.execute(
        "insert_file",
        "/tmp/test.jpg",
        "test.jpg",
        "test",
        ".jpg",
        "/tmp",
        "image",
        "deadbeef",
        12345,
        "2024-01-01T00:00:00",
        "2024-01-01T00:00:00",
        "2024-01-01T00:00:00",
        b"\x01" * 8,  # phash
        b"\x02" * 32,  # orb
        b"\x03" * 2048,  # clip
    )

    print(f"[DEBUG] ({__file__})  Inserted dummy image row with file_id: {file_id}")
    print(f"[DEBUG] ({__file__})  Inserted file_id: {file_id}")

    # Query back using your new SELECT statement
    rows = db.execute("select_all_images_with_clip")
    # Basic assertions
    assert rows is not None
    assert len(rows) >= 1
    assert rows[0][0] == file_id

    print(f"[DEBUG] ({__file__})  Rows returned: {rows}")
    print(
        f"[DEBUG] ({__file__})  Pretty rows returned: \n{[pretty_row(r) for r in rows]} rows"
    )


if __name__ == "__main__":
    print(f"[INFO] ({__file__})  In {__name__} running test_db_basic()...")
    test_db_basic()
