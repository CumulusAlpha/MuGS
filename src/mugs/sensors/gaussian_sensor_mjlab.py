"""
GaussianSensor for mjlab: Batch-first photorealistic rendering

Implements true mjlab.sensor.Sensor interface with:
- Batch rendering: (num_envs, H, W, 3) torch tensors
- 3DGS background + MuJoCo foreground hybrid rendering
- SensorContext integration for efficient GPU rendering
- Two-phase initialization: edit_spec() → initialize()

Author: MuGS Team
Date: 2026-05-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import mujoco
import numpy as np
import torch
from plyfile import PlyData

try:
    from gsplat import rasterization
    GSPLAT_AVAILABLE = True
except ImportError:
    GSPLAT_AVAILABLE = False

try:
    from mjlab.sensor import Sensor, SensorCfg
    import mujoco_warp as mjwarp
    MJLAB_AVAILABLE = True
except ImportError:
    MJLAB_AVAILABLE = False
    # Fallback definitions for development
    from abc import ABC
    from typing import Generic, TypeVar

    T = TypeVar("T")

    @dataclass
    class SensorCfg(ABC):
        name: str
        def build(self): raise NotImplementedError

    class Sensor(ABC, Generic[T]):
        def __init__(self):
            self._cached_data = None
            self._cache_valid = False

if TYPE_CHECKING:
    from mjlab.sensor.sensor_context import SensorContext
    from mjlab.entity import Entity


RenderMode = Literal["hybrid", "3dgs_only", "mujoco_only"]


@dataclass
class GaussianSensorMjlabCfg(SensorCfg):
    """Configuration for batch-first GaussianSensor.

    Follows mjlab sensor config pattern with build() method.
    """

    # Sensor identity
    name: str = "gaussian_sensor"

    # Resolution
    width: int = 640
    height: int = 480

    # Camera setup
    camera_name: str | None = None
    """Existing camera to wrap. If None, creates new camera."""

    parent_body: str | None = None
    """Parent body for new camera. None = worldbody."""

    pos: tuple[float, float, float] = (0.6, -0.8, 1.2)
    """Camera position (world or parent-relative)."""

    quat: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    """Camera orientation (w, x, y, z)."""

    fov_degrees: float = 60.0
    """Vertical field of view in degrees."""

    # 3DGS background
    background_ply_path: Path | None = None
    """Path to pretrained 3DGS PLY file."""

    # Rendering mode
    render_mode: RenderMode = "hybrid"
    """Rendering mode: hybrid (3DGS+MuJoCo), 3dgs_only, or mujoco_only."""

    # Robot masking (for hybrid mode)
    robot_geom_names: list[str] = field(default_factory=lambda: [
        'base_link', 'shoulder_link', 'arm_link', 'forearm_link',
        'palm', 'left_finger_link', 'right_finger_link'
    ])
    """MuJoCo geom names to mask as foreground."""

    # Performance
    cache_background: bool = True
    """Cache static 3DGS background (faster for static scenes)."""

    # Output options
    return_components: bool = False
    """If True, include background/foreground/mask in data."""

    def build(self) -> GaussianSensorMjlab:
        """Build sensor instance from this config."""
        return GaussianSensorMjlab(self)


@dataclass
class GaussianSensorData:
    """Batch sensor output data.

    All tensors have shape (num_envs, height, width, channels).
    Follows mjlab CameraSensorData pattern.
    """

    rgb: torch.Tensor
    """RGB images [num_envs, H, W, 3] (uint8)."""

    background: torch.Tensor | None = None
    """3DGS background [num_envs, H, W, 3] (uint8). None if not enabled."""

    foreground: torch.Tensor | None = None
    """MuJoCo foreground [num_envs, H, W, 3] (uint8). None if not enabled."""

    mask: torch.Tensor | None = None
    """Robot mask [num_envs, H, W, 1] (float32). None if not enabled."""


class GaussianSensorMjlab(Sensor[GaussianSensorData]):
    """Batch-first GaussianSensor compatible with mjlab.

    Implements true mjlab.sensor.Sensor interface:
    - edit_spec(): Add camera to MuJoCo scene spec
    - initialize(): Load 3DGS, cache indices, setup rendering
    - _compute_data(): Batch render all environments

    Data format: (num_envs, height, width, channels) torch.Tensor

    Usage:
        cfg = GaussianSensorMjlabCfg(
            name="gaussian",
            width=640, height=480,
            background_ply_path="kitchen.ply",
            render_mode="hybrid",
        )
        sensor = cfg.build()

        env = Environment(
            model_path="scene.xml",
            sensors=[sensor],
            num_envs=4096,
        )

        obs = env.reset()
        # obs['gaussian'].rgb.shape = (4096, 480, 640, 3)
    """

    requires_sensor_context = True  # Need SensorContext for MuJoCo rendering

    def __init__(self, cfg: GaussianSensorMjlabCfg):
        if not MJLAB_AVAILABLE:
            raise ImportError(
                "mjlab is required for GaussianSensorMjlab. "
                "Use standalone GaussianSensor for non-mjlab usage."
            )

        if not GSPLAT_AVAILABLE:
            raise ImportError("gsplat is required for GaussianSensor")

        super().__init__()
        self.cfg = cfg

        # Camera setup
        self._camera_name = cfg.camera_name if cfg.camera_name else cfg.name
        self._is_wrapping = cfg.camera_name is not None

        # Batch state (initialized in initialize())
        self._num_envs: int = 0
        self._device: str = "cpu"
        self._mj_model: mujoco.MjModel | None = None
        self._mjwarp_model: mjwarp.Model | None = None
        self._mjwarp_data: mjwarp.Data | None = None

        # 3DGS background
        self._gaussians: dict[str, torch.Tensor] | None = None
        self._cached_background: torch.Tensor | None = None

        # MuJoCo rendering (for hybrid/mujoco_only)
        self._ctx: SensorContext | None = None
        self._camera_idx: int = -1
        self._robot_geom_ids: list[int] = []

    @property
    def camera_name(self) -> str:
        """Camera name in MuJoCo model."""
        return self._camera_name

    @property
    def camera_idx(self) -> int:
        """Camera index in compiled model."""
        return self._camera_idx

    # ─────────────────────────────────────────────────────────────
    # mjlab.Sensor Interface Implementation
    # ─────────────────────────────────────────────────────────────

    def edit_spec(
        self,
        scene_spec: mujoco.MjSpec,
        entities: dict[str, Entity],
    ) -> None:
        """Edit scene spec to add camera (if creating new one).

        Called during scene construction before compilation.
        """
        del entities  # Unused

        if self._is_wrapping:
            # Wrapping existing camera - just verify it exists
            cam = scene_spec.camera(self._camera_name)
            if cam is None:
                raise ValueError(f"Camera '{self._camera_name}' not found in scene")
            return

        # Create new camera
        if self.cfg.parent_body is not None:
            parent = scene_spec.body(self.cfg.parent_body)
        else:
            parent = scene_spec.worldbody

        # Convert FOV to radians
        fovy_rad = np.deg2rad(self.cfg.fov_degrees)

        parent.add_camera(
            name=self.cfg.name,
            pos=self.cfg.pos,
            quat=self.cfg.quat,
            fovy=fovy_rad,
            resolution=[self.cfg.width, self.cfg.height],
        )

    def initialize(
        self,
        mj_model: mujoco.MjModel,
        model: mjwarp.Model,
        data: mjwarp.Data,
        device: str,
    ) -> None:
        """Initialize sensor after model compilation.

        - Load 3DGS background
        - Cache camera index
        - Cache robot geom IDs
        - Setup rendering context
        """
        self._mj_model = mj_model
        self._mjwarp_model = model
        self._mjwarp_data = data
        self._device = device

        # Get batch size
        self._num_envs = data.qpos.shape[0]
        print(f"[GaussianSensorMjlab] Initializing for {self._num_envs} environments")

        # Get camera index
        self._camera_idx = mujoco.mj_name2id(
            mj_model, mujoco.mjtObj.mjOBJ_CAMERA, self._camera_name
        )
        if self._camera_idx < 0:
            raise ValueError(f"Camera '{self._camera_name}' not found after compilation")

        print(f"  ✓ Camera '{self._camera_name}' idx={self._camera_idx}")

        # Load 3DGS background
        if self.cfg.background_ply_path is not None:
            print(f"  → Loading 3DGS background: {self.cfg.background_ply_path}")
            self._gaussians = self._load_official_ply(
                self.cfg.background_ply_path,
                torch.device(device)
            )
            print(f"  ✓ Loaded {len(self._gaussians['means']):,} Gaussians")

        # Cache robot geom IDs (for masking)
        if self.cfg.render_mode in ["hybrid", "mujoco_only"]:
            self._robot_geom_ids = []
            for geom_name in self.cfg.robot_geom_names:
                geom_id = mujoco.mj_name2id(
                    mj_model, mujoco.mjtObj.mjOBJ_GEOM, geom_name
                )
                if geom_id >= 0:
                    self._robot_geom_ids.append(geom_id)

            print(f"  ✓ Robot geoms: {len(self._robot_geom_ids)}/{len(self.cfg.robot_geom_names)}")

        print(f"[GaussianSensorMjlab] Initialization complete")

    def _compute_data(self) -> GaussianSensorData:
        """Compute batch sensor data for all environments.

        Returns:
            GaussianSensorData with (num_envs, H, W, C) tensors
        """
        if self.cfg.render_mode == "hybrid":
            return self._compute_hybrid()
        elif self.cfg.render_mode == "3dgs_only":
            return self._compute_3dgs_only()
        else:  # mujoco_only
            return self._compute_mujoco_only()

    # ─────────────────────────────────────────────────────────────
    # Rendering Modes
    # ─────────────────────────────────────────────────────────────

    def _compute_hybrid(self) -> GaussianSensorData:
        """Hybrid mode: 3DGS background + MuJoCo foreground."""

        # 1. Render 3DGS backgrounds (batch)
        backgrounds = self._render_3dgs_batch()  # (N, H, W, 3) uint8

        # 2. Render MuJoCo foregrounds (batch via SensorContext)
        foregrounds, masks = self._render_mujoco_batch()  # (N, H, W, 3), (N, H, W, 1)

        # 3. Composite
        rgb = self._composite_batch(backgrounds, foregrounds, masks)

        # 4. Return data
        if self.cfg.return_components:
            return GaussianSensorData(
                rgb=rgb,
                background=backgrounds,
                foreground=foregrounds,
                mask=masks,
            )
        else:
            return GaussianSensorData(rgb=rgb)

    def _compute_3dgs_only(self) -> GaussianSensorData:
        """3DGS only mode: Just render backgrounds."""
        backgrounds = self._render_3dgs_batch()
        return GaussianSensorData(
            rgb=backgrounds,
            background=backgrounds if self.cfg.return_components else None,
        )

    def _compute_mujoco_only(self) -> GaussianSensorData:
        """MuJoCo only mode: Just render foregrounds."""
        foregrounds, masks = self._render_mujoco_batch()

        if self.cfg.return_components:
            return GaussianSensorData(
                rgb=foregrounds,
                foreground=foregrounds,
                mask=masks,
            )
        else:
            return GaussianSensorData(rgb=foregrounds)

    # ─────────────────────────────────────────────────────────────
    # Batch Rendering Implementation
    # ─────────────────────────────────────────────────────────────

    def _render_3dgs_batch(self) -> torch.Tensor:
        """Render 3DGS backgrounds for all environments.

        Returns:
            RGB batch (num_envs, H, W, 3) uint8 tensor
        """
        if self._gaussians is None:
            # No background loaded - return black
            return torch.zeros(
                (self._num_envs, self.cfg.height, self.cfg.width, 3),
                dtype=torch.uint8,
                device=self._device
            )

        # Check cache
        if self.cfg.cache_background and self._cached_background is not None:
            # TODO: Verify camera poses haven't changed
            return self._cached_background

        # Get camera poses for all environments
        camera_poses = self._get_camera_poses_batch()  # (N, 4, 4)

        # Render each environment
        # TODO: Optimize with batched gsplat when available
        rgb_list = []
        for env_id in range(self._num_envs):
            rgb = self._render_3dgs_single(camera_poses[env_id])
            rgb_list.append(rgb)

        rgb_batch = torch.stack(rgb_list)  # (N, H, W, 3)

        # Cache if enabled
        if self.cfg.cache_background:
            self._cached_background = rgb_batch

        return rgb_batch

    def _render_3dgs_single(self, camera_pose: torch.Tensor) -> torch.Tensor:
        """Render single 3DGS view.

        Args:
            camera_pose: (4, 4) camera-to-world transform

        Returns:
            RGB image (H, W, 3) uint8
        """
        # Build view matrix (world → camera)
        view_matrix = torch.inverse(camera_pose)

        # Camera intrinsics
        fov_y_rad = np.deg2rad(self.cfg.fov_degrees)
        fx = (self.cfg.width / 2) / np.tan(fov_y_rad / 2)
        fy = (self.cfg.height / 2) / np.tan(fov_y_rad / 2)
        cx = self.cfg.width / 2
        cy = self.cfg.height / 2

        K = torch.tensor(
            [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
            dtype=torch.float32,
            device=self._device
        )

        # Render with gsplat
        render_colors, _, _ = rasterization(
            means=self._gaussians['means'],
            quats=self._gaussians['quats'],
            scales=self._gaussians['scales'],
            opacities=self._gaussians['opacities'],
            colors=self._gaussians['colors'],
            viewmats=view_matrix[None],
            Ks=K[None],
            width=self.cfg.width,
            height=self.cfg.height,
            packed=False,
        )

        rgb = render_colors[0].clamp(0, 1)
        return (rgb * 255).to(torch.uint8)

    def _render_mujoco_batch(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Render MuJoCo foregrounds for all environments via SensorContext.

        Returns:
            foregrounds: (num_envs, H, W, 3) uint8
            masks: (num_envs, H, W, 1) float32
        """
        # Get SensorContext from environment
        # NOTE: This requires SensorContext to be set up by Environment
        if self._ctx is None:
            raise RuntimeError(
                "SensorContext not available. "
                "Make sure requires_sensor_context=True and context is injected."
            )

        # Render via context (automatically batched)
        render_out = self._ctx.render(self._camera_idx)

        # Extract RGB and segmentation
        rgb_batch = render_out.rgb  # (N, H, W, 3) uint8
        seg_batch = render_out.segmentation  # (N, H, W, 1) int32

        # Create robot masks
        masks = self._create_robot_masks_batch(seg_batch)  # (N, H, W, 1) float32

        return rgb_batch, masks

    def _composite_batch(
        self,
        backgrounds: torch.Tensor,
        foregrounds: torch.Tensor,
        masks: torch.Tensor
    ) -> torch.Tensor:
        """Composite foregrounds onto backgrounds using masks (batched).

        Args:
            backgrounds: (N, H, W, 3) uint8
            foregrounds: (N, H, W, 3) uint8
            masks: (N, H, W, 1) float32 [0, 1]

        Returns:
            Composited RGB (N, H, W, 3) uint8
        """
        # Expand mask to 3 channels
        masks_3ch = masks.expand(-1, -1, -1, 3)  # (N, H, W, 3)

        # Convert to float for blending
        bg_f = backgrounds.float()
        fg_f = foregrounds.float()

        # Alpha composite: result = bg * (1 - mask) + fg * mask
        composite_f = bg_f * (1 - masks_3ch) + fg_f * masks_3ch

        return composite_f.to(torch.uint8)

    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────

    def _get_camera_poses_batch(self) -> torch.Tensor:
        """Get camera-to-world transforms for all environments.

        Returns:
            Camera poses (num_envs, 4, 4) on device
        """
        # Extract camera transforms from mjwarp.Data
        # cam_xpos: (num_envs, ncam, 3) - camera positions
        # cam_xmat: (num_envs, ncam, 9) - camera rotation matrices (row-major)

        cam_pos = self._mjwarp_data.cam_xpos[:, self._camera_idx, :]  # (N, 3)
        cam_mat = self._mjwarp_data.cam_xmat[:, self._camera_idx, :]  # (N, 9)

        # Reshape rotation matrix from flat (9,) to (3, 3)
        # MuJoCo stores row-major: [r00, r01, r02, r10, r11, r12, r20, r21, r22]
        rot_matrices = cam_mat.reshape(self._num_envs, 3, 3)  # (N, 3, 3)

        # Build 4×4 transformation matrices
        poses = torch.eye(4, device=self._device).unsqueeze(0).expand(self._num_envs, 4, 4).clone()
        poses[:, :3, :3] = rot_matrices  # Rotation
        poses[:, :3, 3] = cam_pos         # Translation

        return poses

    def _create_robot_masks_batch(self, seg_batch: torch.Tensor) -> torch.Tensor:
        """Create robot masks from segmentation IDs (batched).

        Args:
            seg_batch: (num_envs, H, W, 1) int32 geom IDs

        Returns:
            masks: (num_envs, H, W, 1) float32 [0, 1]
        """
        # Create mask tensor
        masks = torch.zeros_like(seg_batch, dtype=torch.float32)

        # Mark robot geoms
        for geom_id in self._robot_geom_ids:
            masks[seg_batch == geom_id] = 1.0

        return masks

    def _load_official_ply(
        self,
        ply_path: Path,
        device: torch.device
    ) -> dict[str, torch.Tensor]:
        """Load official 3DGS PLY format.

        Returns:
            Dictionary of Gaussian parameters as torch tensors on device
        """
        plydata = PlyData.read(ply_path)
        vertex = plydata['vertex']

        # Positions
        positions = np.stack([vertex['x'], vertex['y'], vertex['z']], axis=1)

        # SH DC → RGB
        SH_C0 = 0.28209479177387814
        sh_dc = np.stack([vertex['f_dc_0'], vertex['f_dc_1'], vertex['f_dc_2']], axis=1)
        colors = 0.5 + SH_C0 * sh_dc
        colors = np.clip(colors, 0, 1)

        # Opacity (sigmoid)
        opacities = 1 / (1 + np.exp(-vertex['opacity']))

        # Scales (exp)
        scales = np.exp(np.stack([
            vertex['scale_0'], vertex['scale_1'], vertex['scale_2']
        ], axis=1))

        # Quaternions (normalize)
        quats = np.stack([
            vertex['rot_0'], vertex['rot_1'], vertex['rot_2'], vertex['rot_3']
        ], axis=1)
        quats = quats / np.linalg.norm(quats, axis=1, keepdims=True)

        return {
            'means': torch.from_numpy(positions).float().to(device),
            'colors': torch.from_numpy(colors).float().to(device),
            'opacities': torch.from_numpy(opacities).float().to(device),
            'scales': torch.from_numpy(scales).float().to(device),
            'quats': torch.from_numpy(quats).float().to(device),
        }
