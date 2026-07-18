import click
from dedup.pipeline.ingest import run_ingestion
from dedup.pipeline.parallel_ingest import run_parallel_ingestion
from dedup.db.loader import SQLLoader
from dedup.db.postgres import PostgresDB
from dedup.db.sqlite import SQLiteDB
from dedup.config.settings import DB_BACKEND, DB_PG_URL, DB_SQLITE_PATH
from dedup.core.pathing import to_posix


def get_db():
    loader = SQLLoader(DB_BACKEND)
    if DB_BACKEND == "postgres":
        return PostgresDB(loader, DB_PG_URL)
    return SQLiteDB(loader, str(DB_SQLITE_PATH))


@click.group()
def cli():
    """DeDup CLI — scanning, hashing, ingestion, and duplicate detection."""
    pass


# ---------------------------------------------------------
# INGEST COMMAND
# ---------------------------------------------------------
@cli.command("ingest")
def ingest():
    """Scan all configured roots and ingest into the database."""
    run_ingestion()


# ---------------------------------------------------------
# PARALLEL INGESTION COMMAND
# ---------------------------------------------------------
@cli.command("ingest-parallel")
@click.option(
    "--workers", default=8, show_default=True, help="Number of hashing workers."
)
def ingest_parallel(workers):
    """Parallel scan + hash + DB ingest."""
    run_parallel_ingestion(max_workers=workers)


# ---------------------------------------------------------
# FIND DUPLICATES
# ---------------------------------------------------------
@cli.command("find-duplicates")
def find_duplicates():
    """List duplicate files grouped by hash."""
    db = get_db()
    rows = db.query("select_duplicates_by_hash")

    if not rows:
        click.echo("No duplicates found.")
        return

    for row in rows:
        click.echo(f"\nHash: {row['hash']}")
        click.echo(f"Count: {row['dup_count']}")
        click.echo("Paths:")
        for p in row["paths"]:
            click.echo(f"  - {p}")


# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------
@cli.command()
def stats():
    """Show basic database statistics."""
    db = get_db()

    total = db.query("stats_count_files")[0]["total_files"]
    click.echo(f"Total files: {total}")

    click.echo("\nBy type:")
    rows = db.query("stats_count_by_type")
    for row in rows:
        click.echo(f"  {row['object_type']}: {row['type_count']}")


# ---------------------------------------------------------
# SCAN ONE FILE (no DB)
# ---------------------------------------------------------
@cli.command("scan-one")
@click.argument("path")
def scan_one(path):
    """Scan a single file and print metadata (no DB write)."""
    from dedup.core.scanner import Scanner

    posix = to_posix(path)
    scanner = Scanner([posix])

    for info in scanner.scan():
        click.echo(info)
        return

    click.echo("File not found or not a regular file.")


# ---------------------------------------------------------
# SHOW FILE BY ID
# ---------------------------------------------------------
@cli.command("show-file")
@click.argument("file_id", type=int)
def show_file(file_id):
    """Show a single file record from the database."""
    db = get_db()
    rows = db.query("select_file_by_id", file_id)

    if not rows:
        click.echo("File not found.")
        return

    row = rows[0]
    for key, value in row.items():
        click.echo(f"{key}: {value}")


if __name__ == "__main__":
    cli()
