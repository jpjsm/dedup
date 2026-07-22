def reset_files_table(db):
    """
    Test-only helper. Drops and recreates the 'files' table.
    Never exposed to production SQL loader.
    """

    # Drop table safely
    try:
        cur = db.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS files CASCADE;")
        db.conn.commit()
    except Exception as e:
        print(f"[ERROR] ({__file__}.{__name__})  DROP TABLE failed:", e)

    # Recreate tables using your existing SQL loader
    db.execute("create_tables")
