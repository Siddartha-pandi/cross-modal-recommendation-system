"""
Preprocessing Utilities
CLIP-compatible image and text preprocessing shared across the pipeline.
"""
from io import BytesIO
from typing import Callable, Optional
import logging

import torch
from PIL import Image

logger = logging.getLogger(__name__)


def load_image_from_bytes(raw_bytes: bytes) -> Optional[Image.Image]:
    """
    Decode raw bytes into a PIL Image (RGB).

    Args:
        raw_bytes: Raw image bytes from HTTP response or file read.

    Returns:
        PIL.Image in RGB mode, or None if decoding fails.
    """
    try:
        img = Image.open(BytesIO(raw_bytes)).convert("RGB")
        return img
    except Exception as e:
        logger.debug(f"Failed to decode image bytes: {e}")
        return None


def preprocess_for_clip(
    pil_image: Image.Image,
    clip_preprocess_fn: Callable,
) -> torch.Tensor:
    """
    Apply CLIP's own preprocessing transform to a PIL image.

    Args:
        pil_image: PIL Image (RGB).
        clip_preprocess_fn: The preprocess function returned by clip.load().

    Returns:
        Preprocessed tensor of shape (3, H, W) — ready to unsqueeze and batch.
    """
    return clip_preprocess_fn(pil_image)


def resize_image(
    pil_image: Image.Image,
    max_dim: int = 800,
) -> Image.Image:
    """
    Resize an image so that its longest side ≤ max_dim while preserving
    aspect ratio. CLIP already handles resizing internally, but this
    reduces memory overhead during download processing.
    """
    w, h = pil_image.size
    if max(w, h) <= max_dim:
        return pil_image
    scale = max_dim / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    return pil_image.resize((new_w, new_h), Image.LANCZOS)


def validate_image(pil_image: Image.Image, min_dim: int = 50) -> bool:
    """
    Check that an image meets minimum quality criteria for CLIP embedding.

    Args:
        pil_image: PIL Image to validate.
        min_dim: Minimum pixel dimension (width and height).

    Returns:
        True if the image is usable.
    """
    try:
        w, h = pil_image.size
        return w >= min_dim and h >= min_dim
    except Exception:
        return False
