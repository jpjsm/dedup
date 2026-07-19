import sys
import numpy as np

# --- Test Pillow + imagehash -----------------------------------------------
try:
    from PIL import Image
    import imagehash

    print("Pillow + imagehash: OK")
except Exception as e:
    print("Pillow/imagehash FAILED:", e)
    sys.exit(1)

# --- Test OpenCV + ORB ------------------------------------------------------
try:
    import cv2

    has_orb = hasattr(cv2, "ORB_create")
    print("OpenCV:", cv2.__version__)
    print("OpenCV ORB available:", has_orb)
    if not has_orb:
        raise RuntimeError("cv2.ORB_create is missing (install opencv-contrib-python)")
except Exception as e:
    print("OpenCV FAILED:", e)
    sys.exit(1)

# --- Test NumPy -------------------------------------------------------------
try:
    a = np.zeros((2, 2))
    print("NumPy: OK")
except Exception as e:
    print("NumPy FAILED:", e)
    sys.exit(1)

# --- Test Torch + CUDA ------------------------------------------------------
try:
    import torch

    print("Torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA version:", torch.version.cuda)
except Exception as e:
    print("Torch FAILED:", e)
    sys.exit(1)

# --- Test open_clip ---------------------------------------------------------
try:
    import open_clip

    result = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained=None  # do NOT download weights
    )

    # result may be:
    # (model, preprocess)
    # (model, tokenizer, preprocess)
    # (model, tokenizer, preprocess, metadata)
    # or nested structures

    # Flatten nested tuples/lists
    flat = []
    for item in result:
        if isinstance(item, (tuple, list)):
            flat.extend(item)
        else:
            flat.append(item)

    # Find the preprocess transform
    preprocess = None
    for item in flat:
        # The preprocess transform is a callable with __call__ and __class__.__name__ == 'Compose'
        if callable(item) and hasattr(item, "__call__"):
            preprocess = item
            break

    if preprocess is None:
        raise RuntimeError(
            "Could not locate preprocess transform in open_clip return value"
        )

    print("open_clip: OK (model + preprocess loaded without weights)")

except Exception as e:
    print("open_clip FAILED:", e)
    sys.exit(1)

# --- Test FAISS -------------------------------------------------------------
try:
    import faiss

    print("FAISS:", faiss.__version__)
    try:
        print("FAISS GPUs:", faiss.get_num_gpus())
    except Exception:
        print("FAISS GPU check skipped (CPU build)")
except Exception as e:
    print("FAISS FAILED:", e)
    sys.exit(1)

print("\nAll tests passed — environment is ready.")
