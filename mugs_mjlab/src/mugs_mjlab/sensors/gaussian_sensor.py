"""
GaussianSensor: 3DGS rendering sensor for MJLab

Implements hybrid MuJoCo + 3DGS rendering as an mjlab Sensor.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from pathlib import Path

try:
    import mujoco
except ImportError:
    mujoco = None

try:
    from mugs import MaskConfig
    from mugs.rendering import (
        load_ply_gaussians,
        render_mujoco_rgb,
        render_mujoco_segmentation,
        composite_images,
    )
    from mugs.utils import create_group_masks, composite_with_groups
except ImportError:
    # Fallback for development
    MaskConfig = None
    load_ply_gaussians = None


@dataclass
class GaussianSensorCfg:
    """Configuration for GaussianSensor"""

    camera_name: str
    """MuJoCo camera name"""

    resolution: tuple[int, int] = (640, 480)
    """(width, height)"""

    scene_ply: Optional[str] = None
    """Path to 3DGS scene PLY file"""

    mask_config: Optional[str] = None
    """Path to YAML mask configuration"""

    device: str = "cuda"
    """Device for 3DGS rendering"""

    update_rate: float = 30.0
    """Sensor update rate in Hz"""

    dynamic_objects: Optional[List[str]] = None
    """List of dynamic object body names to sync from MuJoCo"""


class GaussianSensor:
    """
    3DGS rendering sensor for MJLab environments

    Provides hybrid MuJoCo + 3DGS rendering with configurable masking.

    Example:
        ```python
        from mugs_mjlab import GaussianSensor, GaussianSensorCfg

        cfg = GaussianSensorCfg(
            camera_name="camera1",
            resolution=(640, 480),
            scene_ply="kitchen.ply",
            mask_config="mask_config_kitchen.yaml"
        )

        sensor = GaussianSensor(cfg, model, data)
        rgb = sensor.update()  # (H, W, 3)
        ```
    """

    def __init__(
        self,
        cfg: GaussianSensorCfg,
        model: "mujoco.MjModel",
        data: "mujoco.MjData"
    ):
        """
        Initialize GaussianSensor

        Args:
            cfg: Sensor configuration
            model: MuJoCo model
            data: MuJoCo data
        """
        if mujoco is None:
            raise ImportError("mujoco is required for GaussianSensor")

        self.cfg = cfg
        self.model = model
        self.data = data

        # Create MuJoCo renderer
        self.mj_renderer = mujoco.Renderer(
            model,
            height=cfg.resolution[1],
            width=cfg.resolution[0],
            enable_segmentation=True
        )

        # Load 3DGS scene (if provided)
        self.gaussians = None
        if cfg.scene_ply and load_ply_gaussians:
            self.gaussians = load_ply_gaussians(cfg.scene_ply)

        # Load mask configuration
        self.mask_config = None
        if cfg.mask_config and MaskConfig:
            self.mask_config = MaskConfig.from_yaml(cfg.mask_config)
            # Pre-compute geom ID mappings
            from mugs.utils import resolve_geom_ids
            self._group_geom_ids = {}
            for group in self.mask_config.groups:
                self._group_geom_ids[group.name] = resolve_geom_ids(
                    self.model, group
                )

    def update(self) -> "np.ndarray":
        """
        Render one frame

        Returns:
            rgb: (H, W, 3) uint8 RGB image
        """
        import numpy as np

        # 1. Render MuJoCo RGB
        self.mj_renderer.update_scene(self.data, camera=self.cfg.camera_name)
        mujoco_rgb = self.mj_renderer.render().copy()

        # 2. If no 3DGS scene, return MuJoCo only
        if self.gaussians is None or self.mask_config is None:
            return mujoco_rgb

        # 3. Get segmentation
        seg_ids = self.mj_renderer.segmentation.copy()

        # 4. Render 3DGS (placeholder - needs full implementation)
        # TODO: Implement 3DGS rendering with camera extraction
        gs_rgb = np.zeros_like(mujoco_rgb)

        # 5. Create masks
        masks = {}
        for group_name, geom_ids in self._group_geom_ids.items():
            mask = np.zeros_like(seg_ids, dtype=np.uint8)
            for gid in geom_ids:
                mask[seg_ids == gid] = 1
            masks[group_name] = mask

        # 6. Composite
        if composite_with_groups:
            final_rgb = composite_with_groups(
                mujoco_rgb.astype(np.float32),
                gs_rgb.astype(np.float32),
                masks,
                self.mask_config
            )
            return final_rgb.astype(np.uint8)

        return mujoco_rgb
