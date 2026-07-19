# similarity/extractors/clip_extractor.py

import torch
import numpy as np
from PIL import Image
import open_clip

# --- Lazy global model + preprocess ----------------------------------------

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Using the high-level factory that returns (model, preprocess)
_model, _preprocess = open_clip.create_model_from_pretrained(
    model_name="ViT-B-32",
    pretrained="laion2b_s34b_b79k",
)
_model = _model.to(_device)
_model.eval()


def extract_clip_embedding(path: str) -> bytes:
    """
    Compute a CLIP image embedding for the given image path and return it as bytes.

    The embedding is:
      - float32
      - L2-normalized
      - suitable for FAISS (L2 or inner-product)

    Returns:
        bytes: flattened float32 embedding.
    """
    # Load and preprocess image
    img = Image.open(path).convert("RGB")
    img_tensor = _preprocess(img).unsqueeze(0).to(_device)

    with torch.no_grad():
        emb = _model.encode_image(img_tensor)

    # L2-normalize
    emb = emb / emb.norm(dim=-1, keepdim=True)

    # Move to CPU, convert to float32 numpy
    arr = emb.cpu().numpy().astype(np.float32).flatten()

    return arr.tobytes()
