"""Shared optional Pillow image stack for AI service modules."""

# Pillow is optional, but strongly recommended for preprocessing.
try:
    from PIL import Image, ImageOps

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    Image = None
    ImageOps = None
    print("Warning: Pillow not available. Image preprocessing will be limited.")

__all__ = ['PILLOW_AVAILABLE', 'Image', 'ImageOps']
