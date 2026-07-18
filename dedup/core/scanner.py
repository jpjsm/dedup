# dedup/core/scanner.py

from datetime import datetime
import pathlib
import datetime

from .pathing import to_posix
from .classify import classify_extension
from dedup.config.settings import EXCLUDE_SPEC
from dataclasses import dataclass


@dataclass
class FileInfo:
    path: str
    filename: str
    filename_no_ext: str
    extension: str
    parent_folder: str
    object_type: str
    size: int
    created_at: str
    modified_at: str
    scanned_at: str


class Scanner:
    def __init__(self, roots):
        """
        roots: list of directories to scan
        """
        self.roots = roots

    def scan(self):
        """
        Generator that yields FileInfo objects.
        """
        for root in self.roots:
            print(f"[DEBUG] ({__file__}) Scanning root: {root}")
            root_path = pathlib.Path(root)
            if not root_path.exists():
                continue

            for file_path in root_path.rglob("*"):
                if not file_path.is_file():
                    continue

                if EXCLUDE_SPEC.match_file(str(file_path)):
                    continue

                yield self._extract_info(file_path)

    def _extract_info(self, file_path: pathlib.Path) -> FileInfo:
        posix_path = to_posix(str(file_path))

        filename = file_path.name
        extension = file_path.suffix.lower()
        filename_no_ext = file_path.stem
        parent_folder = to_posix(str(file_path.parent))

        object_type = classify_extension(extension)

        stat = file_path.stat()
        size = stat.st_size

        # Convert timestamps to ISO-8601
        created_at = (
            datetime.datetime.fromtimestamp(stat.st_ctime).astimezone().isoformat()
        )
        modified_at = (
            datetime.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat()
        )
        scanned_at = datetime.datetime.now().astimezone().isoformat()

        return FileInfo(
            path=posix_path,
            filename=filename,
            filename_no_ext=filename_no_ext,
            extension=extension,
            parent_folder=parent_folder,
            object_type=object_type,
            size=size,
            created_at=created_at,
            modified_at=modified_at,
            scanned_at=scanned_at,
        )
