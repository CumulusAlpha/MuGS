# MuGS Input Specification

完整的输入数据规范，分为**前置准备**和**运行时输入**两个阶段。

**Last Updated**: 2026-05-02

---

## Table of Contents

1. [前置输入（Pre-requisites）](#前置输入pre-requisites)
2. [运行时输入（Runtime Inputs）](#运行时输入runtime-inputs)
3. [完整数据流](#完整数据流)
4. [示例代码](#示例代码)
5. [文件格式详解](#文件格式详解)

---

## 前置输入（Pre-requisites）

**这些是在运行渲染之前需要准备好的静态资产和配置。**

### 1. 3DGS 对象模型（必需）

**格式**: PLY (Polygon File Format / Stanford Triangle Format)

**内容**: 3D Gaussian Splatting 参数
- Position: (x, y, z) 坐标
- Rotation: 四元数 (qw, qx, qy, qz)
- Scale: (sx, sy, sz) 各轴缩放
- Color: RGB 或 SH 系数
- Opacity: α 透明度
- Spherical Harmonics: 多视角颜色变化

**文件结构**:
```
assets/objects/kitchen/mug_blue.ply
```

**PLY 文件示例** (二进制格式):
```
ply
format binary_little_endian 1.0
element vertex 50000
property float x
property float y
property float z
property float nx
property float ny
property float nz
property float f_dc_0        # RGB color (DC term)
property float f_dc_1
property float f_dc_2
property float f_rest_0      # SH coefficients
property float f_rest_1
...
property float opacity
property float scale_0       # Scale (sx, sy, sz)
property float scale_1
property float scale_2
property float rot_0         # Rotation quaternion
property float rot_1
property float rot_2
property float rot_3
end_header
[Binary data...]
```

**典型文件大小**: 1-50 MB per object

**获取方式**:
- 下载脚本: `python scripts/data_collection/download_assets.py`
- COLMAP 拍摄: 见 `docs/guides/ASSET_ACQUISITION.md`
- Objaverse/NeRF Synthetic: 见资产指南

---

### 2. 对象元数据（推荐）

**格式**: YAML

**用途**: 提供物理属性、分类、许可证等信息

**文件结构**:
```
assets/configs/kitchen/mug_blue.yaml
```

**YAML 格式**:
```yaml
# 基础信息
name: "mug_blue"
category: "kitchen"
description: "Blue ceramic coffee mug with handle"

# 物理属性
size: [0.08, 0.08, 0.10]  # meters [width, depth, height]
mass: 0.3                  # kg
center_of_mass: [0.0, 0.0, 0.05]  # relative to origin

# 渲染属性
bounding_box:
  min: [-0.04, -0.04, 0.0]
  max: [0.04, 0.04, 0.10]
num_gaussians: 50000

# 元数据
source: "objaverse"
object_id: "abc123def456"
captured: "2024-03-15"
license: "CC-BY-4.0"
tags: ["kitchen", "drinkware", "ceramic"]

# 使用建议
recommended_scales: [0.8, 1.0, 1.2]  # for data augmentation
upright_axis: "+z"
stable_poses:  # stable orientations for placement
  - rotation: [0, 0, 0, 1]  # quaternion (identity)
    stability: 1.0
  - rotation: [0.707, 0, 0, 0.707]  # 90° rotation
    stability: 0.3
```

**必需字段**:
- `name`: 对象名称
- `category`: 类别 (kitchen/tools/containers/misc)
- `size`: 物理尺寸 [x, y, z] in meters

**可选但推荐**:
- `mass`: 质量（用于物理模拟）
- `bounding_box`: 包围盒（用于碰撞检测）
- `stable_poses`: 稳定姿态（用于场景生成）

---

### 3. 场景模板配置（可选）

**格式**: YAML

**用途**: 定义场景布局模板（如桌面操作、厨房等）

**文件结构**:
```
configs/scenes/tabletop_manipulation.yaml
```

**YAML 格式**:
```yaml
scene_template:
  name: "tabletop_manipulation"
  type: "manipulation"
  
  # 场景边界
  workspace:
    bounds:
      x: [-0.5, 0.5]  # meters
      y: [-0.4, 0.4]
      z: [0.0, 0.8]
    
  # 表面定义
  surfaces:
    - name: "table"
      type: "plane"
      position: [0.0, 0.0, 0.0]
      normal: [0, 0, 1]
      size: [1.0, 0.8]  # width, depth
      material: "wood"
  
  # 对象放置约束
  placement_rules:
    - category: "kitchen"
      min_objects: 1
      max_objects: 5
      min_spacing: 0.05  # meters between objects
      surface: "table"
      orientation: "upright"  # or "random"
    
    - category: "tools"
      min_objects: 0
      max_objects: 2
      surface: "table"
  
  # 相机配置
  cameras:
    - name: "third_person"
      position: [0.5, 0.0, 0.6]
      look_at: [0.0, 0.0, 0.1]
      fov: 60  # degrees
      resolution: [640, 480]
    
    - name: "wrist_camera"
      type: "attached"
      parent: "robot_wrist"
      offset: [0.0, 0.0, 0.05]
      fov: 90
      resolution: [640, 480]
  
  # 光照（可选，3DGS 自带光照）
  lighting:
    ambient: 0.3
    directional:
      direction: [-0.5, -0.5, -1.0]
      intensity: 0.7
```

---

### 4. 渲染配置（可选）

**格式**: YAML

**用途**: 设置渲染参数

**文件结构**:
```
configs/sensors/gaussian_sensor.yaml
```

**YAML 格式**:
```yaml
sensor_config:
  # 分辨率
  resolution:
    width: 160
    height: 120
  
  # 批量设置
  batch_size: 4096  # parallel cameras
  
  # 相机内参
  intrinsics:
    fov: 60.0  # field of view (degrees)
    # 或者直接指定 K 矩阵:
    # fx: 80.0
    # fy: 80.0
    # cx: 80.0
    # cy: 60.0
  
  # 渲染选项
  rendering:
    background_color: [1.0, 1.0, 1.0]  # RGB [0-1]
    near_plane: 0.01  # meters
    far_plane: 10.0   # meters
    antialiasing: true
  
  # 性能优化
  performance:
    use_half_precision: false  # FP16 for speed
    max_gaussians_per_pixel: 16
    tile_size: 16  # rendering tile size
```

---

### 5. 超分辨率模型（Phase 4）

**格式**: PyTorch checkpoint (.pt / .pth)

**用途**: Stage 2 超分辨率

**文件结构**:
```
models/sr/swinir_light_x4.pth        # 预训练基础模型
models/sr/sim_aware_sr.pt            # 我们微调的模型（Phase 4）
```

**包含内容**:
```python
{
    'model_state_dict': OrderedDict(...),  # 模型参数
    'optimizer_state_dict': OrderedDict(...),  # 优化器状态（训练时）
    'config': {
        'upscale_factor': 4,  # 160x120 -> 640x480
        'in_channels': 3,
        'out_channels': 3,
        'num_features': 64,
        # ... other hyperparameters
    },
    'metrics': {
        'lpips': 0.089,  # 测试集性能
        'psnr': 28.5,
        'ssim': 0.92,
    },
    'training_info': {
        'epoch': 100,
        'best_epoch': 87,
        'training_samples': 10000,
    }
}
```

**下载**:
```bash
python scripts/data_collection/download_assets.py --models swinir-light
```

---

## 运行时输入（Runtime Inputs）

**这些是在每一帧渲染时动态提供的输入。**

### 1. 相机位姿（必需）

**格式**: NumPy array or PyTorch tensor

**Shape**: `(num_cameras, 4, 4)` — SE(3) transformation matrices

**含义**: 每个相机的位置和朝向（世界坐标系）

**数据类型**: 
- NumPy: `np.ndarray` with dtype `float32`
- PyTorch: `torch.Tensor` with dtype `torch.float32`
- Device: GPU (推荐) 或 CPU

**格式**: 4×4 齐次变换矩阵
```python
# 单个相机的 SE(3) 矩阵
pose = [
    [r11, r12, r13, tx],  # rotation + translation
    [r21, r22, r23, ty],
    [r31, r32, r33, tz],
    [0,   0,   0,   1 ]
]

# 批量相机
camera_poses = torch.tensor([
    pose_camera_0,  # shape: (4, 4)
    pose_camera_1,
    pose_camera_2,
    ...
    pose_camera_4095
], dtype=torch.float32, device='cuda')  # shape: (4096, 4, 4)
```

**来源**:
- **MuJoCo 仿真**: 从 `mujoco.MjData.cam_xpos` 和 `cam_xmat` 提取
- **手动设置**: 使用 SE(3) 变换工具
- **轨迹生成**: 圆周轨迹、随机采样等

**坐标系约定**:
- **MuJoCo**: +Z 向上, +X 向前
- **OpenGL/3DGS**: +Y 向上, -Z 向前
- ⚠️ 需要坐标系转换！（见 `src/mugs/utils/transforms.py`）

**示例**:
```python
from mugs.utils.transforms import mujoco_pose_to_opengl

# 从 MuJoCo 获取相机位姿
mj_camera_pos = data.cam_xpos[camera_id]  # (3,)
mj_camera_mat = data.cam_xmat[camera_id]  # (3, 3)

# 转换为 OpenGL 坐标系
gl_pose = mujoco_pose_to_opengl(mj_camera_pos, mj_camera_mat)  # (4, 4)
```

---

### 2. 对象位姿（必需，如果场景有多个对象）

**格式**: NumPy array or PyTorch tensor

**Shape**: `(num_objects, 4, 4)` — SE(3) transformation matrices

**含义**: 每个对象在世界坐标系中的位置和朝向

**数据类型**: 同相机位姿

**格式**: 4×4 齐次变换矩阵（同上）

**示例**:
```python
# 场景中的 3 个对象
object_poses = torch.tensor([
    # Mug at (0.2, 0.0, 0.1), no rotation
    [[1, 0, 0, 0.2],
     [0, 1, 0, 0.0],
     [0, 0, 1, 0.1],
     [0, 0, 0, 1  ]],
    
    # Plate at (-0.1, 0.15, 0.01), no rotation
    [[1, 0, 0, -0.1],
     [0, 1, 0,  0.15],
     [0, 0, 1,  0.01],
     [0, 0, 0,  1   ]],
    
    # Fork at (0.05, -0.1, 0.02), rotated 45° around Z
    [[0.707, -0.707, 0, 0.05],
     [0.707,  0.707, 0, -0.1],
     [0,      0,     1, 0.02],
     [0,      0,     0, 1   ]],
], dtype=torch.float32, device='cuda')  # shape: (3, 4, 4)
```

**来源**:
- **MuJoCo 仿真**: 从 `data.xpos` 和 `data.xmat` 提取
- **场景生成器**: `SceneGenerator.generate()` 输出
- **手动定义**: 固定场景配置

---

### 3. 对象 ID 映射（必需，多对象场景）

**格式**: Python list or NumPy array

**Shape**: `(num_objects,)`

**含义**: 每个对象对应的 3DGS 资产 ID

**数据类型**: `str` or `int`

**示例**:
```python
# 使用字符串 ID（推荐）
object_ids = [
    "kitchen/mug_blue",
    "kitchen/plate_white",
    "kitchen/fork_metal"
]

# 或者使用整数索引
object_ids = [0, 5, 12]  # indices into object library
```

**用途**: 将位姿与对应的 3DGS 模型关联

---

### 4. 场景配置（可选）

**格式**: Python dict

**用途**: 动态场景参数（光照、背景等）

**示例**:
```python
scene_config = {
    'background_color': [0.8, 0.9, 1.0],  # RGB sky blue
    'ambient_light': 0.3,
    'time_of_day': 'afternoon',  # for lighting variation
}
```

---

### 5. 渲染选项（可选）

**格式**: Python dict

**用途**: 覆盖默认渲染设置

**示例**:
```python
render_options = {
    'resolution': (320, 240),  # 临时改变分辨率
    'output_depth': True,      # 是否输出深度图
    'output_segmentation': True,  # 是否输出分割掩码
}
```

---

## 完整数据流

### 可视化流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    前置准备阶段                              │
└─────────────────────────────────────────────────────────────┘

[下载/拍摄]
    ↓
assets/objects/
  ├── kitchen/mug_blue.ply          ← 3DGS 模型
  ├── kitchen/plate_white.ply
  └── ...
    ↓
assets/configs/
  ├── kitchen/mug_blue.yaml         ← 元数据
  └── ...
    ↓
models/sr/
  └── swinir_light_x4.pth           ← SR 模型
    ↓
configs/
  ├── sensors/gaussian_sensor.yaml  ← 渲染配置
  └── scenes/tabletop.yaml          ← 场景模板

┌─────────────────────────────────────────────────────────────┐
│                    运行时阶段                                │
└─────────────────────────────────────────────────────────────┘

[每一帧循环]

1. MuJoCo Simulation Step
   ↓
   physics_state = {
       camera_poses: (N, 4, 4),      ← 从 MuJoCo 提取
       object_poses: (M, 4, 4),      ← 从 MuJoCo 提取
   }

2. 坐标系转换
   ↓
   camera_poses_gl = mujoco_to_opengl(camera_poses)
   object_poses_gl = mujoco_to_opengl(object_poses)

3. Stage 1: GaussianSensor
   ↓
   inputs = {
       'camera_poses': camera_poses_gl,  # (4096, 4, 4)
       'object_poses': object_poses_gl,  # (5, 4, 4)
       'object_ids': ['kitchen/mug_blue', ...],  # (5,)
   }
   ↓
   low_res_images = gaussian_sensor.render(inputs)
   # Output: (4096, 160, 120, 3) RGB images

4. Stage 2: SimAwareSR (可选，Phase 4)
   ↓
   high_res_images = sr_model(low_res_images)
   # Output: (4096, 640, 480, 3) RGB images

5. 输出到 VLA Policy
   ↓
   observations = {
       'rgb': high_res_images,       # (4096, 640, 480, 3)
       'depth': depth_images,        # (4096, 640, 480, 1) - 可选
       'segmentation': seg_masks,    # (4096, 640, 480) - 可选
   }
```

---

## 示例代码

### 完整渲染流程示例

```python
import torch
import numpy as np
from mugs.sensors import GaussianSensor, GaussianSensorCfg
from mugs.assets import ObjectLibrary
from mugs.utils.transforms import mujoco_pose_to_opengl
from mugs.sr_models import SimAwareSR

# ============================================================================
# Phase 1: 前置准备（仅运行一次）
# ============================================================================

# 1. 加载对象库
object_library = ObjectLibrary(assets_dir="assets/objects")
object_library.load_category("kitchen")  # 加载所有厨房对象

# 2. 创建 GaussianSensor
sensor_config = GaussianSensorCfg(
    resolution=(160, 120),
    num_cameras=4096,
    fov=60.0,
    device='cuda'
)
sensor = GaussianSensor(sensor_config, object_library)

# 3. 加载超分辨率模型（Phase 4，可选）
sr_model = SimAwareSR.from_pretrained("models/sr/sim_aware_sr.pt")
sr_model = sr_model.to('cuda')
sr_model.eval()

# ============================================================================
# Phase 2: 设置场景（每个 episode 开始时）
# ============================================================================

# 定义场景中的对象
scene_objects = [
    {'id': 'kitchen/mug_blue', 'pose': np.eye(4)},      # 初始位姿
    {'id': 'kitchen/plate_white', 'pose': np.eye(4)},
    {'id': 'kitchen/fork_metal', 'pose': np.eye(4)},
]

# 注册对象到传感器
sensor.set_scene_objects(scene_objects)

# ============================================================================
# Phase 3: 渲染循环（每一帧）
# ============================================================================

for timestep in range(num_timesteps):
    # 1. MuJoCo 仿真步进
    mujoco.mj_step(model, data)
    
    # 2. 提取相机位姿（从 MuJoCo）
    camera_poses_mj = []
    for i in range(sensor_config.num_cameras):
        pos = data.cam_xpos[i]  # (3,)
        mat = data.cam_xmat[i].reshape(3, 3)  # (3, 3)
        camera_poses_mj.append(
            mujoco_pose_to_opengl(pos, mat)
        )
    camera_poses = torch.tensor(
        np.stack(camera_poses_mj), 
        dtype=torch.float32, 
        device='cuda'
    )  # (4096, 4, 4)
    
    # 3. 提取对象位姿（从 MuJoCo）
    object_poses_mj = []
    for obj in scene_objects:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, obj['name'])
        pos = data.xpos[body_id]
        mat = data.xmat[body_id].reshape(3, 3)
        object_poses_mj.append(
            mujoco_pose_to_opengl(pos, mat)
        )
    object_poses = torch.tensor(
        np.stack(object_poses_mj),
        dtype=torch.float32,
        device='cuda'
    )  # (3, 4, 4)
    
    # 4. Stage 1: 渲染低分辨率图像
    render_inputs = {
        'camera_poses': camera_poses,      # (4096, 4, 4)
        'object_poses': object_poses,      # (3, 4, 4)
    }
    
    with torch.no_grad():
        low_res_images = sensor.render(**render_inputs)
        # Output: (4096, 160, 120, 3) float32 [0-1]
    
    # 5. Stage 2: 超分辨率（可选）
    if sr_model is not None:
        with torch.no_grad():
            # Reshape for SR model: (N, H, W, C) -> (N, C, H, W)
            lr_input = low_res_images.permute(0, 3, 1, 2)  # (4096, 3, 160, 120)
            
            # Upscale
            hr_output = sr_model(lr_input)  # (4096, 3, 640, 480)
            
            # Reshape back: (N, C, H, W) -> (N, H, W, C)
            high_res_images = hr_output.permute(0, 2, 3, 1)  # (4096, 640, 480, 3)
    else:
        # 如果没有 SR 模型，直接上采样
        high_res_images = torch.nn.functional.interpolate(
            low_res_images.permute(0, 3, 1, 2),
            size=(640, 480),
            mode='bilinear',
            align_corners=False
        ).permute(0, 2, 3, 1)
    
    # 6. 传递给 VLA policy
    observations = {
        'rgb': high_res_images,  # (4096, 640, 480, 3)
        'timestep': timestep,
    }
    
    # VLA policy 预测动作
    actions = vla_policy(observations)
    
    # 应用动作到 MuJoCo
    data.ctrl[:] = actions
```

---

### 简化版：单对象单相机

```python
import torch
from mugs.sensors import GaussianSensor, GaussianSensorCfg

# 1. 创建传感器
config = GaussianSensorCfg(
    resolution=(640, 480),
    num_cameras=1,
    fov=60.0,
)
sensor = GaussianSensor(config)

# 2. 加载单个对象
sensor.load_object("assets/objects/kitchen/mug_blue.ply")

# 3. 设置相机位姿
camera_pose = torch.tensor([
    [1, 0, 0, 0.0],   # 相机在 (0, 0, 1)
    [0, 1, 0, 0.0],   # 朝向 (0, 0, 0)
    [0, 0, 1, 1.0],
    [0, 0, 0, 1  ],
], dtype=torch.float32)  # (4, 4)

# 4. 渲染
image = sensor.render(camera_poses=camera_pose[None, :, :])  # (1, 640, 480, 3)

# 5. 保存
import matplotlib.pyplot as plt
plt.imsave("output.png", image[0].cpu().numpy())
```

---

## 文件格式详解

### PLY 文件格式

**ASCII 格式示例** (小文件可用):
```
ply
format ascii 1.0
element vertex 100
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
property float opacity
end_header
0.1 0.2 0.3 255 128 64 0.9
0.2 0.3 0.4 200 150 100 0.8
...
```

**二进制格式** (推荐，文件更小):
```
ply
format binary_little_endian 1.0
element vertex 50000
property float x
property float y
property float z
# ... (properties)
end_header
[Binary data follows]
```

**读取 PLY**:
```python
from plyfile import PlyData

ply_data = PlyData.read("assets/objects/kitchen/mug.ply")
vertex_data = ply_data['vertex'].data

positions = np.stack([vertex_data['x'], vertex_data['y'], vertex_data['z']], axis=1)
# ... extract other properties
```

---

### YAML 配置格式

**最小化配置**:
```yaml
name: "mug_blue"
category: "kitchen"
size: [0.08, 0.08, 0.10]
```

**完整配置**:
```yaml
# 见前面 "对象元数据" 部分
```

**读取 YAML**:
```python
import yaml

with open("assets/configs/kitchen/mug_blue.yaml") as f:
    metadata = yaml.safe_load(f)

object_name = metadata['name']
object_size = metadata['size']  # [0.08, 0.08, 0.10]
```

---

### HDF5 场景格式（Phase 3）

**用途**: 保存完整场景快照

**结构**:
```
scene_001.h5
├── /metadata
│   ├── scene_id: "scene_001"
│   ├── template: "tabletop"
│   └── created: "2026-05-02T10:30:00"
├── /objects
│   ├── /0
│   │   ├── id: "kitchen/mug_blue"
│   │   ├── pose: (4, 4) float32
│   │   └── scale: float32
│   ├── /1
│   │   └── ...
│   └── ...
└── /cameras
    ├── /0
    │   ├── pose: (4, 4) float32
    │   ├── fov: float32
    │   └── resolution: (2,) int32
    └── ...
```

**写入 HDF5**:
```python
import h5py

with h5py.File("assets/scenes/tabletop/scene_001.h5", "w") as f:
    # Metadata
    f.create_dataset("metadata/scene_id", data="scene_001")
    
    # Objects
    for i, obj in enumerate(scene_objects):
        f.create_dataset(f"objects/{i}/id", data=obj['id'])
        f.create_dataset(f"objects/{i}/pose", data=obj['pose'])
    
    # Cameras
    for i, cam in enumerate(cameras):
        f.create_dataset(f"cameras/{i}/pose", data=cam['pose'])
```

**读取 HDF5**:
```python
import h5py

with h5py.File("assets/scenes/tabletop/scene_001.h5", "r") as f:
    scene_id = f["metadata/scene_id"][()]
    
    num_objects = len(f["objects"])
    objects = []
    for i in range(num_objects):
        obj = {
            'id': f[f"objects/{i}/id"][()].decode('utf-8'),
            'pose': f[f"objects/{i}/pose"][:]  # (4, 4) array
        }
        objects.append(obj)
```

---

## 总结

### 前置输入清单

| 输入类型 | 格式 | 必需？ | 来源 | 文件示例 |
|---------|------|--------|------|----------|
| 3DGS 对象模型 | PLY | ✅ 是 | 下载/拍摄 | `mug_blue.ply` |
| 对象元数据 | YAML | 推荐 | 手动编写 | `mug_blue.yaml` |
| 场景模板 | YAML | 可选 | 预定义 | `tabletop.yaml` |
| 渲染配置 | YAML | 可选 | 预定义 | `gaussian_sensor.yaml` |
| SR 模型 | .pt/.pth | Phase 4 | 下载/训练 | `swinir_light.pth` |

### 运行时输入清单

| 输入类型 | Shape | 数据类型 | 必需？ | 来源 |
|---------|-------|----------|--------|------|
| 相机位姿 | `(N, 4, 4)` | Tensor | ✅ 是 | MuJoCo/手动 |
| 对象位姿 | `(M, 4, 4)` | Tensor | 多对象时 | MuJoCo/场景生成 |
| 对象 ID | `(M,)` | List[str] | 多对象时 | 场景定义 |
| 渲染选项 | Dict | Dict | 可选 | 动态覆盖 |

---

**下一步**: 实现 `GaussianSensor` 类（见 Phase 2 TODO.md）

**参考**:
- 技术设计: `docs/design/TECHNICAL_DESIGN.md`
- 资产获取: `docs/guides/ASSET_ACQUISITION.md`
- 快速开始: `docs/guides/QUICK_START.md`
