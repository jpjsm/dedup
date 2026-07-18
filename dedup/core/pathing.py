# dedup/core/pathing.py
import pathlib
import os


def to_posix(path: str) -> str:
    """
    Normalize any OS path into POSIX format.
    Windows backslashes → forward slashes
    Drive letters preserved (C:/...)
    UNC paths preserved (//server/share)
    """
    # Expand user (~) and environment variables
    expanded = os.path.expandvars(os.path.expanduser(path))

    # Convert to pathlib Path and then to POSIX
    return pathlib.Path(expanded).as_posix()
