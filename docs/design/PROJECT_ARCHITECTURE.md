# MuGS项目架构设计

## 📦 模块化设计理念

MuGS采用**核心+扩展**的架构，将通用3DGS渲染能力与特定仿真平台集成解耦：

```
┌─────────────────────────────────────────────────────────────┐
│                         用户应用层                            │
│  VLA Policy / Research Code / Standalone Rendering           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ├─────────────────────────┐
                          ▼                         ▼
            ┌──────────────────────┐    ┌──────────────────────┐
            │   MuGS (核心包)       │    │  MuGS_mjlab (扩展包)  │
            │                      │    │                      │
            │  • 3DGS渲染引擎       │◄───┤  • GaussianSensor    │
            │  • 相机参数管理       │    │  • mjlab集成层       │
            │  • 高斯变换工具       │    │  • ManagerBasedRlEnv │
            │  • 混合渲染系统       │    │    插件              │
            │  • 掩码配置系统       │    └──────────────────────┘
            └──────────────────────┘
                          │
                          ▼
            ┌──────────────────────┐
            │   底层库依赖          │
            │  • gsplat            │
            │  • PyTorch           │
            │  • NumPy             │
            └──────────────────────┘
```

---

## 🎯 包职责划分

### MuGS - 核心渲染包

**定位**: 通用3DGS渲染引擎，平台无关

**核心功能**:
- ✅ 3D高斯渲染（基于gsplat）
- ✅ 相机参数管理
- ✅ SE(3)变换工具
- ✅ 混合渲染（3DGS + 其他渲染器）
- ✅ 掩码配置系统
- ✅ PLY资产加载

**API示例**:
```python
from mugs import GaussianRenderer, load_ply_gaussians, CameraParams

# 加载场景
gaussians = load_ply_gaussians("kitchen.ply")

# 配置相机
camera = CameraParams(
    position=[0, 0, 2],
    lookat=[0, 0, 0],
    up=[0, 0, 1],
    fov=60,
    width=640,
    height=480
)

# 渲染
renderer = GaussianRenderer()
rgb = renderer.render(gaussians, camera)  # (H, W, 3)
```

**安装**:
```bash
pip install mugs
# 或
pip install -e ./mugs
```

**依赖**:
- PyTorch >= 2.0
- gsplat >= 1.0
- NumPy
- PyYAML

---

### MuGS_mjlab - MJLab集成包

**定位**: mjlab仿真环境的3DGS传感器插件

**核心功能**:
- ✅ GaussianSensor API（实现mjlab Sensor接口）
- ✅ 自动从MuJoCo提取相机参数
- ✅ 自动从MuJoCo提取segmentation ID
- ✅ 混合渲染（MuJoCo RGB + 3DGS）
- ✅ 动态物体同步（MuJoCo物理 → 3DGS位姿）
- ✅ 批量并行渲染（多环境支持）

**API示例**:
```python
from mjlab.envs import ManagerBasedRlEnv
from mugs_mjlab import GaussianSensorCfg

# 配置环境
env_cfg = MyEnvCfg()
env_cfg.scene.sensors["rgb_camera"] = GaussianSensorCfg(
    resolution=(640, 480),
    scene_ply="assets/scenes/demo_kitchen/kitchen_scene.json",
    mask_config="assets/configs/mask_config_kitchen.yaml",
    update_rate=30.0  # Hz
)

# 创建环境
env = ManagerBasedRlEnv(cfg=env_cfg)

# 运行仿真（自动渲染）
obs, _ = env.reset()
obs["rgb_camera"]  # (N_env, 640, 480, 3) 混合渲染结果
```

**安装**:
```bash
# 先安装核心包
pip install mugs

# 再安装mjlab扩展
pip install mugs-mjlab
# 或
pip install -e ./mugs_mjlab
```

**依赖**:
- mugs (核心包)
- mjlab >= 0.2.0
- mujoco >= 3.0

---

## 📁 新项目结构

```
mugs-project/                      # 项目根目录
├── README.md                       # 项目总览
├── docs/                           # 共享文档
│   ├── design/                     # 设计文档
│   │   ├── PROJECT_VISION.md
│   │   ├── PROJECT_ARCHITECTURE.md  # 本文档
│   │   ├── TECHNICAL_DESIGN.md
│   │   └── ASSET_FORMAT.md
│   ├── guides/                     # 使用指南
│   │   ├── IMPLEMENTATION.md
│   │   ├── PRETRAINED_MODELS.md
│   │   └── SEGMENT_ID_SYSTEM.md    # 新增：segment ID方案
│   ├── technical/                  # 技术文档
│   │   └── COORDINATE_ALIGNMENT.md
│   └── api/                        # API文档
│       ├── mugs_api.md             # MuGS核心API
│       └── mjlab_sensor_api.md     # MuGS_mjlab API
│
├── mugs/                           # 核心包目录
│   ├── pyproject.toml              # 核心包配置
│   ├── README.md                   # 核心包说明
│   ├── src/mugs/
│   │   ├── __init__.py
│   │   ├── rendering/              # 渲染引擎
│   │   │   ├── __init__.py
│   │   │   ├── gaussian_renderer.py    # 核心渲染器
│   │   │   ├── camera.py               # 相机参数
│   │   │   └── hybrid_compositor.py    # 混合渲染
│   │   ├── utils/                  # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── gaussian_transforms.py  # SE(3)变换
│   │   │   ├── mask_config.py          # 掩码配置
│   │   │   └── ply_loader.py           # PLY加载
│   │   └── version.py
│   └── tests/                      # 核心包测试
│
├── mugs_mjlab/                     # MJLab扩展包目录
│   ├── pyproject.toml              # 扩展包配置
│   ├── README.md                   # 扩展包说明
│   ├── src/mugs_mjlab/
│   │   ├── __init__.py
│   │   ├── sensors/                # Sensor实现
│   │   │   ├── __init__.py
│   │   │   ├── gaussian_sensor.py      # GaussianSensor类
│   │   │   └── gaussian_sensor_cfg.py  # 配置
│   │   ├── utils/                  # MJLab专用工具
│   │   │   ├── __init__.py
│   │   │   ├── mujoco_camera.py        # MuJoCo相机提取
│   │   │   ├── mujoco_segmentation.py  # Segmentation提取
│   │   │   └── sync_physics.py         # 物理同步
│   │   └── version.py
│   └── tests/                      # 扩展包测试
│
├── assets/                         # 共享资产
│   ├── scenes/                     # 3DGS场景
│   │   └── kitchen.ply
│   ├── objects/                    # 3DGS物体
│   └── configs/                    # 配置文件
│       └── mask_config_kitchen.yaml
│
├── examples/                       # 示例代码
│   ├── mugs_core/                  # 核心包示例
│   │   ├── render_standalone.py
│   │   ├── hybrid_rendering.py
│   │   └── camera_trajectory.py
│   └── mugs_mjlab/                 # 扩展包示例
│       ├── basic_sensor.py
│       ├── vla_pick_place.py
│       └── batch_rendering.py
│
├── scripts/                        # 工具脚本
│   ├── data_collection/
│   ├── training/
│   └── evaluation/
│
└── data/                           # 数据目录
    ├── kitchen/                    # Mip-NeRF 360数据
    └── pretrained_models.zip
```

---

## 🔌 依赖关系

```
用户应用
    │
    ├──> mugs_mjlab (可选，仅mjlab用户)
    │       │
    │       ├──> mugs (必需)
    │       └──> mjlab (必需)
    │
    └──> mugs (独立使用)
            │
            ├──> gsplat
            ├──> PyTorch
            └──> NumPy
```

**重要原则**:
- ✅ MuGS **不依赖** mjlab，可独立使用
- ✅ MuGS_mjlab **依赖** MuGS和mjlab
- ✅ 核心算法在MuGS，MuGS_mjlab只做集成

---

## 📦 包配置

### MuGS核心包 (`mugs/pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mugs"
version = "0.1.0"
description = "MuGS: High-performance 3D Gaussian Splatting rendering engine"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "Apache-2.0"}
authors = [
    {name = "MuGS Team", email = "your.email@domain.com"}
]
keywords = ["3d-gaussian-splatting", "rendering", "computer-vision", "robotics"]

dependencies = [
    "torch>=2.0.0",
    "gsplat>=1.0.0",
    "numpy>=1.24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/YOUR_ORG/mugs"
Repository = "https://github.com/YOUR_ORG/mugs"
Documentation = "https://mugs.readthedocs.io"
```

### MuGS_mjlab扩展包 (`mugs_mjlab/pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mugs-mjlab"
version = "0.1.0"
description = "MuGS integration for MJLab simulation framework"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "Apache-2.0"}
authors = [
    {name = "MuGS Team", email = "your.email@domain.com"}
]
keywords = ["mugs", "mjlab", "mujoco", "reinforcement-learning", "sensor"]

dependencies = [
    "mugs>=0.1.0",
    "mjlab>=0.2.0",
    "mujoco>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
]

[project.urls]
Homepage = "https://github.com/YOUR_ORG/mugs"
Repository = "https://github.com/YOUR_ORG/mugs"
```

---

## 🚀 使用场景

### 场景1: 独立渲染（仅使用MuGS）

```python
# 适用于：数据可视化、离线渲染、研究实验
from mugs import GaussianRenderer, load_ply_gaussians, CameraParams

gaussians = load_ply_gaussians("scene.ply")
camera = CameraParams.from_intrinsics(
    fx=500, fy=500, cx=320, cy=240,
    width=640, height=480,
    position=[0, 0, 2],
    rotation=[0, 0, 0, 1]  # quat
)

renderer = GaussianRenderer(device="cuda")
rgb = renderer.render(gaussians, camera)
```

### 场景2: 混合渲染（MuGS + 其他渲染器）

```python
# 适用于：机器人仿真、合成数据生成
from mugs import GaussianRenderer, HybridCompositor
from mugs.utils import MaskConfig, create_group_masks

# 渲染3DGS背景
gs_rgb = gs_renderer.render(gaussians, camera)

# 渲染机器人（从其他渲染器）
robot_rgb = other_renderer.render()
seg_ids = other_renderer.get_segmentation()

# 混合
config = MaskConfig.from_yaml("mask_config.yaml")
masks = create_group_masks(seg_ids, config)
compositor = HybridCompositor(config)
final_rgb = compositor.composite(robot_rgb, gs_rgb, masks)
```

### 场景3: MJLab强化学习（MuGS_mjlab）

```python
# 适用于：VLA训练、RL策略学习
from mjlab.envs import ManagerBasedRlEnv
from mugs_mjlab import GaussianSensorCfg

env_cfg = MyEnvCfg()
env_cfg.scene.sensors["rgb"] = GaussianSensorCfg(
    resolution=(640, 480),
    scene_ply="kitchen.ply",
    mask_config="mask_config_kitchen.yaml"
)

env = ManagerBasedRlEnv(cfg=env_cfg, num_envs=4096)
obs = env.reset()
# obs["rgb"]: (4096, 640, 480, 3) 批量混合渲染
```

---

## 🔄 数据流

### MuGS核心包数据流

```
PLY文件 → load_ply_gaussians() → Gaussians Dict
                                       │
相机参数 → CameraParams ───────────────┤
                                       ▼
                              GaussianRenderer.render()
                                       │
                                       ▼
                                  RGB图像 (H,W,3)
```

### MuGS_mjlab数据流

```
MJLab Environment Step
    │
    ├──> MuJoCo Physics Update
    │       │
    │       ├──> body poses (xpos, xquat)
    │       └──> camera params (cam_xpos, cam_xmat)
    │
    └──> GaussianSensor.update()
            │
            ├──> 提取相机参数 (mujoco_camera.py)
            ├──> 渲染MuJoCo RGB + Segmentation
            ├──> 同步3DGS物体位姿 (sync_physics.py)
            ├──> 渲染3DGS场景 (GaussianRenderer)
            ├──> 提取掩码 (mujoco_segmentation.py)
            └──> 混合渲染 (HybridCompositor)
                    │
                    ▼
            返回观测 {"rgb": (N_env, H, W, 3)}
```

---

## 📋 迁移计划

### Step 1: 重构现有代码（1-2天）

```bash
# 1. 创建新目录结构
mkdir -p mugs/src/mugs/{rendering,utils}
mkdir -p mugs_mjlab/src/mugs_mjlab/{sensors,utils}

# 2. 移动核心代码到mugs/
# rendering.py → mugs/rendering/gaussian_renderer.py
# mask_config.py → mugs/utils/mask_config.py
# gaussian_transforms.py → mugs/utils/gaussian_transforms.py

# 3. 移动mjlab集成到mugs_mjlab/
# gaussian_sensor.py → mugs_mjlab/sensors/gaussian_sensor.py

# 4. 保留现有文档和资产
# docs/ 和 assets/ 保持不变
```

### Step 2: 配置包管理（0.5天）

```bash
# 1. 创建pyproject.toml
# mugs/pyproject.toml
# mugs_mjlab/pyproject.toml

# 2. 配置包导入
# mugs/src/mugs/__init__.py
# mugs_mjlab/src/mugs_mjlab/__init__.py
```

### Step 3: 更新文档和示例（0.5天）

```bash
# 1. 更新README
# 2. 创建SEGMENT_ID_SYSTEM.md
# 3. 更新API文档
# 4. 重构examples/
```

### Step 4: 测试和验证（1天）

```bash
# 1. 独立安装测试
pip install -e mugs/
pip install -e mugs_mjlab/

# 2. 运行现有benchmarks验证性能
python scripts/evaluation/benchmark_full_pipeline.py

# 3. 运行示例代码
python examples/mugs_mjlab/basic_sensor.py
```

---

## 💡 设计优势

### 1. **解耦关注点**
- 核心算法与平台集成分离
- 便于维护和测试

### 2. **灵活使用**
- 可以只用MuGS做渲染
- 可以扩展到其他仿真平台（Isaac Gym, Isaac Sim）

### 3. **易于发布**
- 独立版本控制
- 独立PyPI发布
- 清晰的依赖关系

### 4. **性能优化**
- MuGS专注渲染性能
- MuGS_mjlab专注批量并行

### 5. **社区友好**
- 通用API吸引更多用户
- mjlab集成服务特定社区

---

## 📌 下一步行动

1. ✅ 创建SEGMENT_ID_SYSTEM.md文档
2. 🔄 重构代码到新目录结构
3. 🔄 配置pyproject.toml
4. 🔄 更新README和API文档
5. 🔄 迁移示例代码
6. 🔄 运行测试验证

---

**文档版本**: v1.0  
**最后更新**: 2026-05-02  
**维护者**: MuGS Team
