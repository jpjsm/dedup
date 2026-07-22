from typing import Generator

from PIL import Image
import os
from pathlib import Path


def get_tiff_files(folder_path):
    """
    Returns a list of all .tiff files in the given folder (non-recursive).
    Case-insensitive match.
    """
    valid_exts = {".tif", ".tiff"}
    try:
        folder = Path(folder_path)

        # Validate folder existence
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        if not folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder_path}")

        # List all .tiff files (case-insensitive)
        tiff_files = [
            f
            for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in valid_exts
        ]

        return tiff_files

    except Exception as e:
        print(f"Error: {e}")
        return []


def create_image_from_list(image_list, output_path):
    """
    Create a single image from a list of images and save it to the specified output path.

    :param image_list: List of image file paths to be combined.
    :param output_path: Path where the combined image will be saved.
    """
    Image.MAX_IMAGE_PIXELS = None
    images = [Image.open(img).convert("RGB") for img in image_list]

    # First image is the base; the rest get appended
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        compression="tiff_deflate",  # or "tiff_lzw"
    )

    print(f"Multi-page TIFF {output_path} created successfully!")


def list_tiff_pages(tiff_path) -> int:
    Image.MAX_IMAGE_PIXELS = None
    total_frames = 0
    with Image.open(tiff_path) as img:
        print(f"TIFF contains {img.n_frames} pages:")
        total_frames = img.n_frames
        for i in range(img.n_frames):
            img.seek(i)
            print(f" - Page {i}: size={img.size}, mode={img.mode}")
    return total_frames


def extract_tiff_pages(tiff_path, output_dir):
    Image.MAX_IMAGE_PIXELS = None
    os.makedirs(output_dir, exist_ok=True)

    with Image.open(tiff_path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            out_path = os.path.join(output_dir, f"page_{i+1}.png")
            img.save(out_path, compression="tiff_deflate")
            print(f"Saved {out_path}")


def extract_single_page(tiff_path, page_number):
    Image.MAX_IMAGE_PIXELS = None
    output_path = (
        f"{Path(tiff_path).parent}/{Path(tiff_path).stem}_page_{page_number + 1}.tiff"
    )
    with Image.open(tiff_path) as img:
        img.seek(page_number)
        img.save(output_path)


def iter_tiff_pages(tiff_path) -> Generator[Image.Image, None, None]:
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(tiff_path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            yield img.copy()


def tiff_page_info(tiff_path):
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(tiff_path) as img:
        for i in range(img.n_frames):
            img.seek(i)
            print(f"Page {i}:")
            print("  Size:", img.size)
            print("  Mode:", img.mode)
            print("  Info:", img.info)


if __name__ == "__main__":
    folder_path = "C:/Users/alterego/OneDrive/Documents/Scanned Documents"  # Change to your folder path
    image_files = get_tiff_files(folder_path)

    if image_files:
        # Example usage
        output_file = (
            "C:/Users/alterego/OneDrive/Documents/Scanned Documents/multi_page.tiff"
        )
        create_image_from_list(image_files, output_file)

        extract_tiff_pages(
            output_file,
            "C:/Users/alterego/OneDrive/Documents/Scanned Documents/extracted_pages",
        )

        total_frames = list_tiff_pages(output_file)
        print(f"Total frames in the TIFF file: {total_frames}")
        # generating images through generator
        for img in iter_tiff_pages(output_file):
            img.save(
                f"C:/Users/alterego/OneDrive/Documents/Scanned Documents/extracted_pages/page_{img.tell() + 1}.png",
                compression="tiff_deflate",
            )

        tiff_page_info(output_file)
