# MuGS 项目总览

## 项目定位

**MuGS** (MuJoCo + 3D Gaussian Splatting) 是一个**照片级机器人仿真渲染系统**，用于生成视觉语言动作（Vision-Language-Action, VLA）模型的训练数据。

### 核心目标

弥合 **Sim2Real 差距**：让仿真环境的视觉观测接近真实照片，同时保持物理仿真的准确性。

### 关键创新

- **两阶段渲染架构**：MuJoCo 渲染前景（机器人、物体）+ 3DGS 渲染背景（真实场景扫描）
- **5000+ FPS 性能**：通过 CPU-GPU 并行实现高速渲染
- **无缝集成**：Drop-in API 适配 MuJoCo、mjlab、IsaacLab 等主流框架
- **可选超分辨率**：AI 上采样模块，低分辨率渲染 + 高分辨率输出

---

## 仓库结构

```
mugs/
├── src/mugs/                 # 核心库代码
│   ├── sensors/              # 渲染传感器
│   │   ├── gaussian_sensor.py        # 独立使用 API
│   │   └── gaussian_sensor_mjlab.py  # mjlab 批量渲染
│   └── postprocess/          # 后处理模块
│       └── super_resolution.py       # AI 超分辨率 (可选)
│
├── examples/                 # 示例脚本
│   ├── yam_standalone_demo.py        # YAM 机械臂 Demo
│   ├── sr_pipeline_demo.py           # 超分辨率 Demo
│   ├── quality_comparison_demo.py    # 质量对比
│   └── use_external_assets.py        # 外部资产使用
│
├── scripts/                  # 工具脚本
│   ├── download_sr_models.py         # 下载超分模型
│   └── download_external_assets.py   # 下载 3DGS 场景
│
├── docs/                     # 文档
│   ├── API_REFERENCE.md              # 完整 API 文档
│   ├── API_QUICKSTART.md             # 快速上手 (中文)
│   ├── SUPER_RESOLUTION.md           # 超分辨率指南
│   ├── CAMERA_ALIGNMENT_FIX.md       # 相机对齐技术细节
│   ├── EXTERNAL_ASSETS.md            # 外部资产使用
│   ├── design/DESIGN.md              # 系统设计文档
│   └── PROJECT_STATUS.md             # 项目当前状态
│
├── data/                     # 数据目录
│   ├── pretrained/           # 预训练资源
│   │   ├── kitchen/          # INRIA 厨房 3DGS 场景
│   │   └── sr/               # 超分辨率模型权重
│   └── external/             # 外部下载资产
│
├── tests/                    # 测试用例
├── docs/images/showcase/     # 展示材料 (moved)
├── README.md                 # 项目主页
└── TODO.md                   # 开发计划
```

---

## 核心组件

### 1. 渲染引擎

#### `GaussianSensor` - 独立渲染 API

用于单环境、演示、可视化场景。

**特点**:
- 简单易用的 Python API
- 支持三种渲染模式：`hybrid`（混合）、`3dgs_only`（纯背景）、`mujoco_only`（纯 MuJoCo）
- 返回完整组件（RGB、前景、背景、遮罩）

**性能**: ~5000 FPS (640×480 混合渲染)

**使用场景**:
- 调试和可视化
- 单帧渲染
- Demo 演示

#### `GaussianSensorMjlab` - 批量渲染 API

用于 RL 训练、大规模数据生成场景。

**特点**:
- mjlab 框架集成
- 支持 4096+ 并行环境
- GPU 加速批量渲染

**性能**: ~10ms/batch (4096 envs × 320×240)

**使用场景**:
- 强化学习训练
- 大规模数据集生成
- 多环境并行仿真

---

### 2. 后处理模块

#### `SuperResolution` - AI 超分辨率 (可选)

基于 Real-ESRGAN 的照片级上采样。

**特点**:
- 模块化设计，完全可选
- 懒加载（首次调用时才加载模型）
- 批处理支持
- 三种预训练模型可选

**性能**: ~100ms/frame (320×240 → 1280×960)

**使用场景**:
- 训练时用低分辨率（快）
- 评估时用高分辨率（照片级）
- 视频生成和展示

**安装**:
```bash
pip install realesrgan basicsr
python scripts/download_sr_models.py --model RealESRGAN_x4plus
```

---

## 关键技术

### 1. 两阶段渲染架构

```
┌─────────────┐      ┌─────────────┐
│   MuJoCo    │      │    3DGS     │
│  Renderer   │      │  Renderer   │
│  (CPU/GPU)  │      │   (GPU)     │
└──────┬──────┘      └──────┬──────┘
       │                    │
       │ Foreground         │ Background
       │ (Robot, Obj)       │ (Real Scene)
       │                    │
       └────────┬───────────┘
                │
          ┌─────▼─────┐
          │   Alpha   │
          │ Composite │
          └─────┬─────┘
                │
           ┌────▼────┐
           │  Output │
           │  (RGB)  │
           └─────────┘
```

**优势**:
- MuJoCo 保证物理准确性
- 3DGS 提供照片级背景
- Alpha 合成自动处理遮挡

### 2. 相机参数对齐

自动处理 MuJoCo 和 3DGS 之间的相机参数转换：

- **FOV 处理**：识别 MuJoCo `<compiler angle="radian"/>` 指令
- **坐标系转换**：MuJoCo (+Z forward) ↔ OpenGL (-Z forward)
- **视图矩阵**：从相机位置和旋转自动构建

详见 `docs/CAMERA_ALIGNMENT_FIX.md`

### 3. 自动前景分割

三种方式指定前景物体：

1. **按几何体名称** (推荐):
   ```python
   robot_geom_names=["link1", "link2", "gripper"]
   ```

2. **按几何体 ID** (无名几何体):
   ```python
   robot_geom_ids=[0, 1, 2, 5, 6]
   ```

3. **按 Body 前缀** (命名空间场景):
   ```python
   robot_body_prefixes=["robot/", "table/", "obj_"]
   ```

### 4. 背景相机跟踪

动态相机场景下，3DGS 背景相机自动跟随 MuJoCo 相机运动：

```python
R_align = R_gs0 · R_mj0ᵀ
pos_t   = pos_gs0 + R_align · (pos_mj_t − pos_mj_0)
R_t     = R_align · R_mj_t
```

详见 `README.md` § "Hybrid render — bg cam tracks MuJoCo head"

---

## 资产支持

### 预训练场景

1. **INRIA Kitchen**
   - 来源：mip-NeRF 360 数据集
   - 规模：1.85M 高斯点
   - 分辨率：640×480
   - 位置：`data/pretrained/kitchen/`

### 外部资产（可下载）

1. **GS-Playground**
   - 多样化室内外场景
   - 高质量 3DGS 重建
   - 下载：`python scripts/download_external_assets.py gs-playground`

2. **DISCOVERSE**
   - 机器人操作任务场景
   - 配套 MuJoCo XML
   - 下载：`python scripts/download_external_assets.py discoverse`
   - 注意：压缩格式需转换（见 `docs/DISCOVERSE_ISSUES.md`）

3. **Bridge-GS**
   - 真实机器人数据集的 3DGS 重建
   - 下载：`python scripts/download_external_assets.py bridge-gs`

### 自定义场景

支持任何 COLMAP / Nerfstudio 输出的 3DGS PLY 文件。

---

## 使用场景

### 1. 单环境演示/调试

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig

sensor = GaussianSensor(GaussianSensorConfig(
    width=640, height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["link1", "link2"],
))

rgb = sensor.render(model, data, "main_camera")
```

### 2. RL 训练（批量）

```python
from mjlab import Environment
from mugs.sensors import GaussianSensorMjlabCfg

cfg = GaussianSensorMjlabCfg(
    name="camera", width=224, height=224,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["link1", "link2"],
)

env = Environment("scene.xml", sensors=[cfg.build()], num_envs=4096)
obs = env.reset()
# obs['camera'].rgb: (4096, 224, 224, 3) torch.Tensor
```

### 3. 视频生成 + 超分辨率

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig
from mugs.postprocess import SuperResolution, SuperResolutionConfig

# 低分辨率渲染
sensor = GaussianSensor(GaussianSensorConfig(width=320, height=240, ...))
sr = SuperResolution(SuperResolutionConfig())

for step in range(360):
    img_lr = sensor.render(model, data, "camera")  # 快速渲染
    img_hr = sr.upscale(img_lr)                     # 照片级上采样
    save_frame(img_hr)
```

---

## 性能数据

| 配置 | 分辨率 | 模式 | FPS | 延迟 | 备注 |
|------|--------|------|-----|------|------|
| 单环境 | 640×480 | hybrid | 5000 | 0.2ms | 无 SR |
| 单环境 | 320×240 | hybrid | 10000 | 0.1ms | 无 SR |
| 单环境 | 320×240 → 1280×960 | hybrid + SR | 10 | 100ms | Real-ESRGAN 4x |
| 批量 (4096 envs) | 320×240 | hybrid | 409 batch/s | 2.4ms/batch | mjlab |

**测试环境**: RTX 4090, AMD Ryzen 9 7950X

---

## 文档指引

### 快速开始
1. **[README.md](../README.md)** - 项目主页，安装和快速开始
2. **[API_QUICKSTART.md](API_QUICKSTART.md)** - 中文快速上手指南

### API 文档
3. **[API_REFERENCE.md](API_REFERENCE.md)** - 完整 API 参考
4. **[SUPER_RESOLUTION.md](SUPER_RESOLUTION.md)** - 超分辨率详细指南

### 技术细节
5. **[design/DESIGN.md](design/DESIGN.md)** - 系统架构设计（12k 字）
6. **[CAMERA_ALIGNMENT_FIX.md](CAMERA_ALIGNMENT_FIX.md)** - 相机对齐技术细节
7. **[EXTERNAL_ASSETS.md](EXTERNAL_ASSETS.md)** - 外部资产使用教程

### 其他
8. **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - 当前项目状态
9. **[TODO.md](../TODO.md)** - 开发计划
10. **[DISCOVERSE_ISSUES.md](DISCOVERSE_ISSUES.md)** - DISCOVERSE 集成已知问题

---

## 开发状态

### 已完成 ✅

- [x] 两阶段渲染架构
- [x] MuJoCo + 3DGS 混合渲染
- [x] 独立 API (`GaussianSensor`)
- [x] mjlab 批量渲染 (`GaussianSensorMjlab`)
- [x] 自动相机参数对齐
- [x] 三种前景分割方式
- [x] 动态背景相机跟踪
- [x] 超分辨率模块（Real-ESRGAN）
- [x] 外部资产下载脚本
- [x] 完整文档和示例
- [x] 测试覆盖

### 进行中 🚧

- [ ] DISCOVERSE 压缩格式解包器
- [ ] 更多预训练场景
- [ ] 性能优化（CUDA kernel）

### 计划中 📋

- [ ] IsaacLab 集成
- [ ] Multi-view 渲染
- [ ] 动态物体的 3DGS
- [ ] 论文发表（RSS/CoRL 2026）

---

## 引用

如果您使用 MuGS，请引用：

```bibtex
@article{mugs2026,
  title={MuGS: Photorealistic Simulation for Vision-Language-Action Models},
  author={},
  journal={},
  year={2026}
}
```

---

## 相关项目

- **MuJoCo**: https://mujoco.org/
- **3D Gaussian Splatting**: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/
- **gsplat**: https://github.com/nerfstudio-project/gsplat
- **Real-ESRGAN**: https://github.com/xinntao/Real-ESRGAN
- **mjlab**: (内部项目)
- **AndroidTwin**: (内部项目，G1 人形机器人基准)

---

## 许可证

MIT License

---

**最后更新**: 2026-05-03
