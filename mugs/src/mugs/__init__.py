"""
MuGS: High-performance 3D Gaussian Splatting Rendering Engine

Platform-agnostic core rendering library for 3D Gaussian Splatting.
"""

__version__ = "0.1.0"

from mugs.rendering import GaussianRenderer
from mugs.utils import MaskConfig, MaskGroup

__all__ = [
    "GaussianRenderer",
    "MaskConfig",
    "MaskGroup",
]
