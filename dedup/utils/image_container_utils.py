from PIL import Image
from pathlib import Path
import os
from typing import Generator, List

MULTI_FRAME_EXTS = {".tif", ".tiff", ".gif", ".webp", ".ico", ".psd"}


def get_container_files(folder_path: str) -> List[Path]:
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Invalid folder: {folder_path}")

    return [
        f
        for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in MULTI_FRAME_EXTS
    ]


def list_container_frames(path: str) -> int:
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as img:
        print(f"{path} contains {img.n_frames} frames:")
        for i in range(img.n_frames):
            img.seek(i)
            print(f" - Frame {i}: size={img.size}, mode={img.mode}")
        return img.n_frames


def extract_container_frames(path: str, output_dir: str):
    Image.MAX_IMAGE_PIXELS = None
    os.makedirs(output_dir, exist_ok=True)

    with Image.open(path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            out_path = os.path.join(output_dir, f"frame_{i+1}.png")
            img.save(out_path)
            print(f"Saved {out_path}")


def extract_single_frame(path: str, frame_number: int):
    Image.MAX_IMAGE_PIXELS = None
    base = Path(path)
    out_path = base.with_name(f"{base.stem}_frame_{frame_number+1}.png")

    with Image.open(path) as img:
        img.seek(frame_number)
        img.save(out_path)
        print(f"Saved {out_path}")


def iter_container_frames(path: str) -> Generator[Image.Image, None, None]:
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            yield img.copy()


if __name__ == "__main__":
    folder = "C:/Users/alterego/OneDrive/Documents/Scanned Documents"

    files = get_container_files(folder)
    print("Found container files:", files)

    for f in files:
        print("\n--- Testing:", f)
        total = list_container_frames(str(f))
        print("Total frames:", total)

        extract_container_frames(str(f), f"{folder}/extracted_{f.stem}")
