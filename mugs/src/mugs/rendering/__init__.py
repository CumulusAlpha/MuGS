"""
3D Gaussian Splatting rendering module

Core rendering functionality for 3DGS.
"""

from mugs.rendering.core import (
    load_ply_gaussians,
    render_mujoco_rgb,
    render_mujoco_segmentation,
    create_robot_mask,
    composite_images,
    extract_mujoco_camera_params,
)

# Placeholder for future GaussianRenderer class
class GaussianRenderer:
    """Platform-agnostic 3DGS renderer (to be implemented)"""
    pass

__all__ = [
    "GaussianRenderer",
    "load_ply_gaussians",
    "render_mujoco_rgb",
    "render_mujoco_segmentation",
    "create_robot_mask",
    "composite_images",
    "extract_mujoco_camera_params",
]
