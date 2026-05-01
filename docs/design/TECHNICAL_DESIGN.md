# Technical Design Specification

> **Comprehensive technical architecture for MJLab-3DGS-VLA**

**Version**: 1.0  
**Last Updated**: 2026-05-01  
**Status**: Design Phase

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [GaussianSensor Implementation](#2-gaussiansensor-implementation)
3. [3DGS Asset Pipeline](#3-3dgs-asset-pipeline)
4. [Super-Resolution Model](#4-super-resolution-model)
5. [Procedural Scene Generation](#5-procedural-scene-generation)
6. [Data Formats](#6-data-formats)
7. [Performance Optimization](#7-performance-optimization)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. System Architecture

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MJLab Environment                         │
│  ┌────────────┐  ┌──────────┐  ┌─────────────────────┐     │
│  │ MJWarp Sim │─▶│ Entities │─▶│ ObservationManager  │     │
│  │ (Physics)  │  │ (Robots) │  │  ┌───────────────┐  │     │
│  └────────────┘  └──────────┘  │  │ GaussianSensor│  │     │
│                                  │  └───────┬───────┘  │     │
│                                  └──────────┼──────────┘     │
└─────────────────────────────────────────────┼────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │         GaussianSensor Module                        │
                    ├──────────────────────────────────────────────────────┤
                    │                                                       │
                    │  ┌─────────────────────────────────────────────┐    │
                    │  │ 1. Asset Loading (initialize)                │    │
                    │  │   - Load object 3DGS .ply files              │    │
                    │  │   - Load scene background .ply               │    │
                    │  │   - Build splat_to_body_idx mapping          │    │
                    │  │   - Upload to GPU (one-time)                 │    │
                    │  └─────────────────────────────────────────────┘    │
                    │                     ↓                                 │
                    │  ┌─────────────────────────────────────────────┐    │
                    │  │ 2. Per-Step Rendering (_compute_data)        │    │
                    │  │   a. Read body_link_pose_w from entities     │    │
                    │  │      → (N_env, N_body, 7) torch.Tensor       │    │
                    │  │                                               │    │
                    │  │   b. Apply SE(3) to Gaussians (batched)      │    │
                    │  │      • splat_world_means = transform_points  │    │
                    │  │      • splat_world_quats = quat_mul          │    │
                    │  │                                               │    │
                    │  │   c. Prepare camera parameters               │    │
                    │  │      • Intrinsics (fx, fy, cx, cy)           │    │
                    │  │      • Extrinsics (ego-centric from robot)   │    │
                    │  │                                               │    │
                    │  │   d. gsplat.rasterization()                  │    │
                    │  │      → (N_env, H, W, 3) low-res RGB          │    │
                    │  └─────────────────────────────────────────────┘    │
                    │                     ↓                                 │
                    │  ┌─────────────────────────────────────────────┐    │
                    │  │ 3. Optional Super-Resolution                 │    │
                    │  │   if self.cfg.enable_sr:                     │    │
                    │  │     rgb = self.sr_model(rgb)                 │    │
                    │  │   → (N_env, H_high, W_high, 3)               │    │
                    │  └─────────────────────────────────────────────┘    │
                    │                     ↓                                 │
                    │  ┌─────────────────────────────────────────────┐    │
                    │  │ 4. Return CameraSensorData                   │    │
                    │  │   data.image = rgb                           │    │
                    │  │   data.timestamp = env.current_time          │    │
                    │  └─────────────────────────────────────────────┘    │
                    │                                                       │
                    └───────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
Physics Step (MJWarp)
      ↓
Update body poses: xpos, xquat
      ↓
GaussianSensor.initialize() [once]
  • Load assets → GPU
  • Build mappings
      ↓
GaussianSensor._compute_data() [per step]
  ├─ Read body_link_pose_w (GPU tensor, zero-copy)
  ├─ Transform Gaussians (GPU kernel)
  ├─ Rasterize (gsplat, GPU)
  ├─ [Optional] Super-resolve (SR model, GPU)
  └─ Return RGB tensor (GPU-resident)
      ↓
ObservationManager
  • Collects all obs terms
  • Returns to env.step()
      ↓
Policy network (runs on same GPU)
```

**Key Property**: Entire pipeline is GPU-resident. No CPU↔GPU transfers except initial asset upload.

---

## 2. GaussianSensor Implementation

### 2.1 Class Structure

```python
# src/mjlab_3dgs/sensors/gaussian_sensor.py

from mjlab.sensor import Sensor, SensorCfg
from dataclasses import dataclass
import torch
import gsplat

@dataclass
class GaussianSensorCfg(SensorCfg):
    """Configuration for GaussianSensor."""
    
    class_type: type = GaussianSensor
    
    # Camera parameters
    resolution: tuple[int, int] = (160, 120)  # (width, height)
    fov: float = 60.0  # degrees
    near: float = 0.01
    far: float = 100.0
    
    # Asset paths
    object_library_path: str = "assets/objects/library.yaml"
    scene_background_path: str = "assets/scenes/default.ply"
    
    # Rendering options
    enable_sr: bool = True
    sr_model_path: str = "configs/sr/simawaresr.yaml"
    sr_scale: int = 4  # 160×120 → 640×480
    
    # Performance tuning
    max_sh_degree: int = 3
    gaussian_prune_threshold: float = 0.5  # Opacity threshold
    fp16_rendering: bool = True


class GaussianSensor(Sensor):
    """3D Gaussian Splatting sensor for photorealistic rendering."""
    
    cfg: GaussianSensorCfg
    
    def __init__(self, cfg: GaussianSensorCfg):
        super().__init__(cfg)
        
        # Will be initialized in initialize()
        self.object_library = None
        self.scene_background = None
        self.splat_to_body_idx = None
        self.camera_intrinsics = None
        self.sr_model = None
        
    def __str__(self) -> str:
        return f"GaussianSensor(res={self.cfg.resolution}, sr={self.cfg.enable_sr})"
    
    # ─────────────────────────────────────────────────────────────
    # Sensor Interface Implementation
    # ─────────────────────────────────────────────────────────────
    
    def edit_spec(self, scene_cfg: dict) -> dict:
        """
        Called during scene creation to modify MJCF if needed.
        For GaussianSensor, we don't modify MJCF (external rendering).
        """
        return scene_cfg
    
    def initialize(self, env):
        """
        Called after MuJoCo model compilation, before first step.
        This is where we upload assets to GPU.
        """
        super().initialize(env)
        
        # 1. Load object library
        from mjlab_3dgs.assets import load_object_library
        self.object_library = load_object_library(
            self.cfg.object_library_path,
            device=self.device
        )
        
        # 2. Load scene background
        self.scene_background = self._load_scene_ply(
            self.cfg.scene_background_path
        )
        
        # 3. Build splat_to_body_idx mapping
        self.splat_to_body_idx = self._build_splat_body_mapping(env)
        
        # 4. Compute camera intrinsics
        w, h = self.cfg.resolution
        fov_rad = np.deg2rad(self.cfg.fov)
        fx = fy = (w / 2) / np.tan(fov_rad / 2)
        cx, cy = w / 2, h / 2
        self.camera_intrinsics = torch.tensor(
            [fx, fy, cx, cy], device=self.device
        )
        
        # 5. Load super-resolution model
        if self.cfg.enable_sr:
            from mjlab_3dgs.sr_models import load_sr_model
            self.sr_model = load_sr_model(
                self.cfg.sr_model_path,
                device=self.device
            )
            self.sr_model.eval()
        
        print(f"[GaussianSensor] Initialized:")
        print(f"  - Objects: {len(self.object_library)} items")
        print(f"  - Total splats: {self._count_total_splats()}")
        print(f"  - Resolution: {self.cfg.resolution}")
        print(f"  - SR enabled: {self.cfg.enable_sr}")
    
    def _compute_data(self, env) -> dict:
        """
        Per-step rendering. Returns dict with 'image' key.
        """
        # 1. Get body poses from mjlab entities
        # Assumes env has entity named "robot"
        robot = env.scene["robot"]
        body_poses_w = robot.data.body_link_pose_w  # (N_env, N_body, 7)
        
        # 2. Transform Gaussians to world frame
        from mjlab_3dgs.utils import transform_gaussians_batch
        gaussians_world = transform_gaussians_batch(
            self.object_library,
            self.scene_background,
            body_poses_w,
            self.splat_to_body_idx,
            device=self.device
        )
        # Returns: GaussianData with .means, .quats, .scales, .opacity, .sh
        
        # 3. Get camera extrinsics (ego-centric, from robot head)
        camera_poses = self._get_camera_poses(robot)  # (N_env, 7)
        
        # 4. Rasterize with gsplat
        rgb = self._rasterize_batch(
            gaussians_world,
            camera_poses,
            resolution=self.cfg.resolution
        )  # (N_env, H, W, 3) in [0, 1]
        
        # 5. Super-resolution (optional)
        if self.cfg.enable_sr and self.sr_model is not None:
            with torch.no_grad():
                rgb = self.sr_model(rgb)  # (N_env, H*scale, W*scale, 3)
        
        # 6. Return as CameraSensorData-compatible dict
        return {
            "image": rgb,  # (N_env, H, W, 3)
            "timestamp": env.current_time
        }
    
    # ─────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────
    
    def _load_scene_ply(self, ply_path: str):
        """Load background scene 3DGS from .ply file."""
        from plyfile import PlyData
        import torch
        
        plydata = PlyData.read(ply_path)
        vertex = plydata['vertex']
        
        means = torch.tensor(
            np.stack([vertex['x'], vertex['y'], vertex['z']], axis=-1),
            device=self.device,
            dtype=torch.float32 if not self.cfg.fp16_rendering else torch.float16
        )
        
        # ... similarly parse quats, scales, opacity, SH coefficients
        
        return {
            'means': means,
            'quats': quats,
            'scales': scales,
            'opacity': opacity,
            'sh_coeffs': sh_coeffs
        }
    
    def _build_splat_body_mapping(self, env):
        """
        Build mapping from each Gaussian splat to its parent body index.
        
        Returns:
            splat_to_body_idx: torch.LongTensor, shape (total_splats,)
                               -1 for background splats (static)
        """
        total_splats = self._count_total_splats()
        mapping = torch.full(
            (total_splats,), -1, dtype=torch.long, device=self.device
        )
        
        offset = 0
        # Background splats: stay at -1 (static)
        offset += len(self.scene_background['means'])
        
        # Object splats: map to body index
        for obj_name, obj_data in self.object_library.items():
            n_splats = len(obj_data['means'])
            body_idx = self._find_body_idx(env, obj_name)
            mapping[offset : offset + n_splats] = body_idx
            offset += n_splats
        
        return mapping
    
    def _find_body_idx(self, env, obj_name: str) -> int:
        """Find MuJoCo body index by name."""
        robot = env.scene["robot"]
        body_names = robot.body_names
        if obj_name in body_names:
            return body_names.index(obj_name)
        else:
            raise ValueError(f"Object '{obj_name}' not found in robot bodies")
    
    def _get_camera_poses(self, robot):
        """
        Get ego-centric camera poses from robot head/eyes.
        
        Returns:
            camera_poses: (N_env, 7) torch.Tensor (pos + quat)
        """
        # Assumes robot has a body named "head" or "camera_link"
        head_pose = robot.data.body_link_pose_w[:, robot.body_names.index("head")]
        return head_pose
    
    def _rasterize_batch(self, gaussians, camera_poses, resolution):
        """
        Batched 3DGS rasterization using gsplat.
        
        Args:
            gaussians: GaussianData with .means, .quats, etc.
            camera_poses: (N_env, 7)
            resolution: (width, height)
        
        Returns:
            rgb: (N_env, H, W, 3) torch.Tensor
        """
        from gsplat import rasterization
        
        N_env = camera_poses.shape[0]
        width, height = resolution
        
        # Build camera matrices for each env
        cam_mats = self._build_camera_matrices(camera_poses)  # (N_env, 4, 4)
        
        # gsplat rasterization (batched)
        rgb, alpha = rasterization(
            means=gaussians.means,      # (N_env, N_splat, 3)
            quats=gaussians.quats,       # (N_env, N_splat, 4)
            scales=gaussians.scales,     # (N_env, N_splat, 3)
            opacities=gaussians.opacity, # (N_env, N_splat, 1)
            colors=gaussians.sh_coeffs,  # (N_env, N_splat, C_sh)
            viewmats=cam_mats,           # (N_env, 4, 4)
            Ks=self.camera_intrinsics,   # (4,) or (N_env, 4)
            width=width,
            height=height,
            sh_degree=self.cfg.max_sh_degree
        )
        
        return rgb  # (N_env, H, W, 3)
    
    def _count_total_splats(self):
        """Count total number of Gaussian splats."""
        count = len(self.scene_background['means'])
        for obj_data in self.object_library.values():
            count += len(obj_data['means'])
        return count
```

### 2.2 SE(3) Transform Utils

```python
# src/mjlab_3dgs/utils/gaussian_transforms.py

import torch

def transform_gaussians_batch(
    object_library: dict,
    scene_background: dict,
    body_poses_w: torch.Tensor,  # (N_env, N_body, 7)
    splat_to_body_idx: torch.Tensor,  # (N_splat,)
    device: torch.device
):
    """
    Apply SE(3) transforms to Gaussians based on body poses.
    
    Args:
        object_library: Dict of {obj_name: gaussian_data}
        scene_background: Static background Gaussians
        body_poses_w: World poses of all bodies, (N_env, N_body, 7)
                      Format: [x, y, z, qw, qx, qy, qz]
        splat_to_body_idx: Mapping (N_splat,), -1 = static
    
    Returns:
        GaussianData with transformed means and quats, shape (N_env, N_splat, ...)
    """
    N_env, N_body, _ = body_poses_w.shape
    
    # Concatenate all splats (background + objects)
    all_means = []
    all_quats = []
    all_scales = []
    all_opacity = []
    all_sh = []
    
    # Background (static, repeat for each env)
    bg_means = scene_background['means'].unsqueeze(0).expand(N_env, -1, -1)
    all_means.append(bg_means)
    # ... similarly for quats, scales, etc.
    
    # Objects (need transforms)
    for obj_name, obj_data in object_library.items():
        local_means = obj_data['means']  # (N_obj_splat, 3)
        local_quats = obj_data['quats']  # (N_obj_splat, 4)
        
        # Find which body this object belongs to
        body_idx = ... # from splat_to_body_idx
        
        # Get body poses for this object
        T_w = body_poses_w[:, body_idx, :]  # (N_env, 7)
        
        # Transform means: world_pos = T_w @ local_pos
        world_means = transform_points_batch(T_w, local_means)  # (N_env, N_obj_splat, 3)
        
        # Transform quats: world_quat = T_w_quat * local_quat
        world_quats = quat_mul_batch(T_w[:, 3:], local_quats)  # (N_env, N_obj_splat, 4)
        
        all_means.append(world_means)
        all_quats.append(world_quats)
        # scales and opacity unchanged
    
    # Concatenate along splat dimension
    final_means = torch.cat(all_means, dim=1)  # (N_env, N_total_splat, 3)
    final_quats = torch.cat(all_quats, dim=1)  # (N_env, N_total_splat, 4)
    # ...
    
    return GaussianData(
        means=final_means,
        quats=final_quats,
        scales=final_scales,
        opacity=final_opacity,
        sh_coeffs=final_sh
    )


def transform_points_batch(poses: torch.Tensor, points: torch.Tensor):
    """
    Apply SE(3) transforms to points.
    
    Args:
        poses: (N, 7) [x, y, z, qw, qx, qy, qz]
        points: (M, 3) local coordinates
    
    Returns:
        world_points: (N, M, 3)
    """
    N = poses.shape[0]
    M = points.shape[0]
    
    pos = poses[:, :3]    # (N, 3)
    quat = poses[:, 3:]   # (N, 4)
    
    # Rotate points by quaternion
    points_exp = points.unsqueeze(0).expand(N, -1, -1)  # (N, M, 3)
    rotated = quat_rotate_vector(quat, points_exp)      # (N, M, 3)
    
    # Translate
    world_points = rotated + pos.unsqueeze(1)           # (N, M, 3)
    
    return world_points


def quat_mul_batch(q1: torch.Tensor, q2: torch.Tensor):
    """Quaternion multiplication (batched)."""
    # q1: (N, 4), q2: (M, 4) → result: (N, M, 4)
    # Hamilton product implementation
    ...


def quat_rotate_vector(quat: torch.Tensor, vec: torch.Tensor):
    """Rotate vector by quaternion (batched)."""
    # v' = q * v * q^{-1}
    ...
```

---

## 3. 3DGS Asset Pipeline

### 3.1 Asset Format

**Object Library YAML:**

```yaml
# assets/objects/ycb_library.yaml

objects:
  - name: "003_cracker_box"
    ply_path: "assets/objects/ycb/003_cracker_box.ply"
    mesh_path: "assets/objects/ycb/003_cracker_box.obj"
    scale: 1.0
    metadata:
      category: "food"
      mass_kg: 0.411
      dimensions_m: [0.16, 0.21, 0.07]
  
  - name: "004_sugar_box"
    ply_path: "assets/objects/ycb/004_sugar_box.ply"
    mesh_path: "assets/objects/ycb/004_sugar_box.obj"
    scale: 1.0
    metadata:
      category: "food"
      mass_kg: 0.514
      dimensions_m: [0.09, 0.18, 0.13]
  
  # ... 50+ objects
```

**Background Scene PLY:**
- Standard 3DGS .ply format (compatible with gsplat, Nerfstudio)
- Contains: positions, normals, SH coefficients, opacity, scale, rotation

### 3.2 Reconstruction Pipeline

```bash
# scripts/data_collection/reconstruct_object.sh

#!/bin/bash
# Reconstruct single object as 3DGS

OBJECT_NAME=$1
INPUT_DIR="data/raw/${OBJECT_NAME}"
OUTPUT_DIR="assets/objects/ycb"

# 1. Run COLMAP (structure from motion)
colmap automatic_reconstructor \
  --image_path ${INPUT_DIR}/images \
  --workspace_path ${INPUT_DIR}/colmap \
  --camera_model PINHOLE

# 2. Train 3DGS with gsplat
python scripts/training/train_gsplat.py \
  --colmap-dir ${INPUT_DIR}/colmap \
  --output ${OUTPUT_DIR}/${OBJECT_NAME}.ply \
  --iterations 30000 \
  --eval

# 3. Extract mesh for physics
python scripts/data_collection/extract_mesh.py \
  --ply ${OUTPUT_DIR}/${OBJECT_NAME}.ply \
  --output ${OUTPUT_DIR}/${OBJECT_NAME}.obj \
  --method tsdf

# 4. Align mesh and Gaussian centers
python scripts/data_collection/align_assets.py \
  --ply ${OUTPUT_DIR}/${OBJECT_NAME}.ply \
  --mesh ${OUTPUT_DIR}/${OBJECT_NAME}.obj \
  --output ${OUTPUT_DIR}/${OBJECT_NAME}_aligned.yaml

echo "Reconstruction complete: ${OBJECT_NAME}"
```

---

## 4. Super-Resolution Model

### 4.1 Architecture

```python
# src/mjlab_3dgs/sr_models/simawaresr.py

import torch
import torch.nn as nn

class SimAwareSR(nn.Module):
    """
    Super-resolution model trained on sim+real paired data.
    Based on SwinIR-light architecture.
    """
    
    def __init__(
        self,
        upscale: int = 4,
        in_chans: int = 3,
        img_size: tuple = (120, 160),  # H, W
        embed_dim: int = 60,
        depths: list = [6, 6, 6, 6],
        num_heads: list = [6, 6, 6, 6],
        window_size: int = 8
    ):
        super().__init__()
        
        self.upscale = upscale
        
        # Shallow feature extraction
        self.conv_first = nn.Conv2d(in_chans, embed_dim, 3, 1, 1)
        
        # Deep feature extraction (Swin Transformer blocks)
        self.layers = nn.ModuleList()
        for i, (depth, num_head) in enumerate(zip(depths, num_heads)):
            layer = RSTB(  # Residual Swin Transformer Block
                dim=embed_dim,
                depth=depth,
                num_heads=num_head,
                window_size=window_size
            )
            self.layers.append(layer)
        
        # Reconstruction
        self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
        self.conv_before_upsample = nn.Sequential(
            nn.Conv2d(embed_dim, 64, 3, 1, 1),
            nn.LeakyReLU(inplace=True)
        )
        
        # Upsampling
        self.upsample = Upsample(upscale, 64)
        self.conv_last = nn.Conv2d(64, in_chans, 3, 1, 1)
    
    def forward(self, x):
        """
        Args:
            x: (B, H, W, 3) or (B, 3, H, W) low-res image in [0, 1]
        
        Returns:
            out: (B, H*upscale, W*upscale, 3) high-res image
        """
        # Handle (B, H, W, 3) → (B, 3, H, W)
        if x.dim() == 4 and x.shape[-1] == 3:
            x = x.permute(0, 3, 1, 2)
        
        B, C, H, W = x.shape
        
        # Feature extraction
        feat = self.conv_first(x)
        
        # Deep features
        for layer in self.layers:
            feat = layer(feat)
        
        feat = self.conv_after_body(feat) + feat  # Residual
        
        # Upsample
        feat = self.conv_before_upsample(feat)
        out = self.upsample(feat)
        out = self.conv_last(out)
        
        # Back to (B, H', W', 3)
        out = out.permute(0, 2, 3, 1)
        
        return torch.clamp(out, 0, 1)
```

### 4.2 Training Script

```python
# scripts/training/train_sr.py

import torch
from torch.utils.data import DataLoader
from mjlab_3dgs.sr_models import SimAwareSR
from mjlab_3dgs.datasets import SimRealPairedDataset

def train_sr_model(cfg):
    # 1. Load dataset
    train_dataset = SimRealPairedDataset(
        sim_low_res_dir="data/sim/low_res",
        sim_high_res_dir="data/sim/high_res",
        real_high_res_dir="data/real/images",
        split="train"
    )
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    
    # 2. Initialize model
    model = SimAwareSR(upscale=4).cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-4)
    
    # 3. Loss functions
    from lpips import LPIPS
    lpips_loss = LPIPS(net='alex').cuda()
    mse_loss = nn.MSELoss()
    
    # 4. Training loop
    for epoch in range(100):
        for batch in train_loader:
            low_res = batch['low_res'].cuda()   # (B, 160, 120, 3)
            high_res = batch['high_res'].cuda()  # (B, 640, 480, 3)
            is_real = batch['is_real']           # (B,) bool
            
            # Forward
            pred = model(low_res)
            
            # Loss
            loss_pixel = mse_loss(pred, high_res)
            loss_perceptual = lpips_loss(
                pred.permute(0, 3, 1, 2),
                high_res.permute(0, 3, 1, 2)
            ).mean()
            
            # Weighted loss (higher weight on real data)
            weight = torch.where(is_real, 2.0, 1.0)
            loss = (loss_pixel + 0.1 * loss_perceptual) * weight.mean()
            
            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        print(f"Epoch {epoch}: loss={loss.item():.4f}")
    
    # 5. Save model
    torch.save(model.state_dict(), "checkpoints/simawaresr.pth")
```

---

## 5. Procedural Scene Generation

### 5.1 Scene Sampler

```python
# src/mjlab_3dgs/scene_gen/procedural_sampler.py

class ProceduralSceneSampler:
    """Generate diverse scenes by procedurally placing objects."""
    
    def __init__(
        self,
        object_library: dict,
        background_scenes: list,
        mujoco_model,
        device
    ):
        self.object_library = object_library
        self.backgrounds = background_scenes
        self.mj_model = mujoco_model
        self.device = device
    
    def sample_scene(self, num_objects: int = None):
        """
        Sample a random scene configuration.
        
        Returns:
            scene_cfg: dict with {
                'background': background_3dgs,
                'objects': [
                    {'name': str, 'pose': (7,), 'gaussian_data': dict},
                    ...
                ]
            }
        """
        # 1. Sample background
        bg = random.choice(self.backgrounds)
        
        # 2. Sample number of objects
        if num_objects is None:
            num_objects = random.randint(5, 15)
        
        # 3. Sample object types
        object_names = random.sample(
            list(self.object_library.keys()),
            k=num_objects
        )
        
        # 4. Sample poses (physics-based collision-free placement)
        poses = self._sample_collision_free_poses(
            object_names,
            num_attempts=100
        )
        
        # 5. Build scene config
        objects = []
        for name, pose in zip(object_names, poses):
            objects.append({
                'name': name,
                'pose': pose,  # (7,) [x, y, z, qw, qx, qy, qz]
                'gaussian_data': self.object_library[name]
            })
        
        return {
            'background': bg,
            'objects': objects
        }
    
    def _sample_collision_free_poses(self, object_names, num_attempts=100):
        """
        Use MuJoCo to sample collision-free object placements.
        """
        import mujoco
        
        poses = []
        for obj_name in object_names:
            for attempt in range(num_attempts):
                # Sample random position on table
                x = random.uniform(-0.3, 0.3)
                y = random.uniform(-0.3, 0.3)
                z = 0.8  # table height
                
                # Random orientation
                quat = random_quaternion()
                
                pose = np.array([x, y, z, *quat])
                
                # Check collision with existing objects
                if self._is_collision_free(pose, poses):
                    poses.append(pose)
                    break
            else:
                print(f"Warning: Failed to place {obj_name} after {num_attempts} attempts")
        
        return torch.tensor(poses, device=self.device)
    
    def _is_collision_free(self, new_pose, existing_poses):
        """Simple sphere-based collision check."""
        # Use object bounding spheres for fast check
        for exist_pose in existing_poses:
            dist = np.linalg.norm(new_pose[:3] - exist_pose[:3])
            if dist < 0.1:  # Min separation
                return False
        return True
```

---

## 6. Data Formats

### 6.1 Gaussian PLY Format

```
ply
format binary_little_endian 1.0
element vertex 100000
property float x
property float y
property float z
property float nx
property float ny
property float nz
property float f_dc_0           # SH degree 0, channel 0 (R)
property float f_dc_1           # SH degree 0, channel 1 (G)
property float f_dc_2           # SH degree 0, channel 2 (B)
property float f_rest_0         # SH degree 1+, channel 0
...
property float f_rest_44        # Up to degree 3 = 45 coeffs total
property float opacity
property float scale_0          # Log scale x
property float scale_1          # Log scale y
property float scale_2          # Log scale z
property float rot_0            # Quaternion w
property float rot_1            # Quaternion x
property float rot_2            # Quaternion y
property float rot_3            # Quaternion z
end_header
<binary data>
```

### 6.2 Episode Data Format

For VLA training, episodes saved as:

```python
# data/episodes/episode_00001.hdf5

{
    'observations': {
        'rgb': (T, H, W, 3),           # uint8
        'proprio': (T, D_proprio),      # float32
    },
    'actions': (T, D_action),           # float32
    'language': str,                    # "pick up the red box"
    'metadata': {
        'scene_config': {...},
        'success': bool,
        'episode_length': int
    }
}
```

---

## 7. Performance Optimization

### 7.1 Memory Management

| Component | Memory (GB) @ 4096 envs |
|-----------|------------------------|
| MuJoCo Warp physics | ~8 GB |
| 3DGS assets (100k splats) | ~2 GB |
| Rendered images (low-res) | ~0.5 GB |
| SR model weights | ~0.1 GB |
| SR intermediate activations | ~4 GB |
| **Total** | **~15 GB** |

**Optimizations**:
- FP16 rendering: halves Gaussian memory
- Gradient checkpointing in SR: reduces activations
- Lazy SR: only upscale frames fed to policy (not all renders)

### 7.2 Compute Profiling

Expected breakdown (A100 GPU, 4096 envs):

| Stage | Time (ms) | FPS |
|-------|-----------|-----|
| MuJoCo physics step | 0.5 | - |
| Transform Gaussians (SE(3)) | 0.2 | - |
| gsplat rasterization (160×120) | 0.8 | 5000 |
| Super-resolution (batched) | 50 | - |
| **Total (w/ SR)** | 51.5 | 194 (per-env: 79k) |
| **Total (w/o SR)** | 1.5 | 2730 |

**Note**: SR can be run asynchronously or skipped for non-policy frames.

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/unit/test_gaussian_transforms.py

def test_transform_points_identity():
    """Identity transform should not change points."""
    poses = torch.tensor([[0, 0, 0, 1, 0, 0, 0]])  # Identity
    points = torch.randn(100, 3)
    
    result = transform_points_batch(poses, points)
    
    assert torch.allclose(result[0], points, atol=1e-5)


def test_transform_points_translation():
    """Pure translation."""
    poses = torch.tensor([[1, 2, 3, 1, 0, 0, 0]])
    points = torch.tensor([[0, 0, 0], [1, 0, 0]])
    
    result = transform_points_batch(poses, points)
    
    expected = torch.tensor([[[1, 2, 3], [2, 2, 3]]])
    assert torch.allclose(result, expected, atol=1e-5)
```

### 8.2 Integration Tests

```python
# tests/integration/test_gaussian_sensor.py

def test_gaussian_sensor_in_env():
    """End-to-end test: sensor in mjlab env."""
    from mjlab.envs import ManagerBasedRlEnv
    
    cfg = get_test_env_cfg()
    cfg.scene.sensors["rgb"] = GaussianSensorCfg(
        resolution=(160, 120),
        object_library_path="tests/assets/test_library.yaml"
    )
    
    env = ManagerBasedRlEnv(cfg)
    obs, _ = env.reset()
    
    assert "rgb" in obs
    assert obs["rgb"].shape == (env.num_envs, 120, 160, 3)
    assert obs["rgb"].min() >= 0 and obs["rgb"].max() <= 1
```

### 8.3 Benchmark Tests

```python
# tests/integration/test_performance.py

def test_rendering_fps():
    """Validate rendering FPS meets target."""
    env = create_benchmark_env(num_envs=4096)
    
    start = time.time()
    for _ in range(100):
        env.step(env.action_space.sample())
    elapsed = time.time() - start
    
    fps = (100 * 4096) / elapsed
    assert fps >= 5000, f"FPS {fps} below target 5000"
```

---

## Next Steps

1. **Implement GaussianSensor skeleton** (Phase 1, Week 1)
2. **Validate gsplat integration** (Phase 1, Week 1-2)
3. **Build object asset pipeline** (Phase 2, Week 3-5)
4. **Train SimAwareSR model** (Phase 4, Week 8-10)
5. **Run end-to-end VLA task** (Phase 3, Week 6-7)

---

**Document Status**: Draft  
**Reviewed By**: TBD  
**Approval**: Pending implementation
