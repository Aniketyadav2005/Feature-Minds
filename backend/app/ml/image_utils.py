"""
Image blurring + disk persistence helpers, shared by the analyze feature.
"""
import os
import uuid

import numpy as np
from PIL import Image, ImageFilter


def blur_image(image_np: np.ndarray, radius: int = 15) -> np.ndarray:
    pil_img = Image.fromarray(image_np)
    return np.array(pil_img.filter(ImageFilter.GaussianBlur(radius=radius)))


def save_image(image_np: np.ndarray, directory: str, prefix: str = "") -> str:
    """Save a numpy image to `directory` with a unique filename; returns the path."""
    os.makedirs(directory, exist_ok=True)
    name = f"{prefix}{uuid.uuid4().hex}.jpg"
    path = os.path.join(directory, name)
    Image.fromarray(image_np).convert("RGB").save(path, "JPEG", quality=90)
    return path
