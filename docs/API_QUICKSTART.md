# MuGS API 快速上手指南

**目标读者**: AI Agent / 开发者  
**阅读时间**: 5 分钟  
**前置知识**: Python, MuJoCo 基础

---

## 📦 安装

```bash
# 1. 克隆仓库
git clone <repo-url>
cd mugs

# 2. 安装依赖
pip install -e .
pip install gsplat==1.5.3
pip install mujoco>=3.8.0

# 3. (可选) 安装 mjlab 用于批量渲染
pip install tyro warp-lang mujoco-warp
```

---

## 🚀 核心 API

### 方式 1: 独立使用 (单环境)

```python
import mujoco
from mugs.sensors import GaussianSensor

# 1. 加载 MuJoCo 场景
model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# 2. 创建传感器
sensor = GaussianSensor(
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",  # 3DGS 背景
    render_mode="hybrid",  # "hybrid" | "3dgs_only" | "mujoco_only"
    robot_geom_names=['panda_link0', 'panda_link1', 'panda_link2'],  # 机器人部件
)

# 3. 渲染一帧
result = sensor.render(
    model, 
    data, 
    camera_name="main_camera",
    return_components=True,  # 返回各组件
)

# 4. 获取结果
rgb = result['rgb']              # (H, W, 3) numpy.ndarray, uint8
background = result['background'] # (H, W, 3) 3DGS 背景
foreground = result['foreground'] # (H, W, 3) MuJoCo 前景
mask = result['mask']            # (H, W, 1) 机器人遮罩
```

**适用场景**: 单环境演示、调试、可视化

---

### 方式 2: 批量使用 (多环境并行)

```python
from mjlab import Environment
from mugs.sensors import GaussianSensorMjlabCfg

# 1. 配置传感器
cfg = GaussianSensorMjlabCfg(
    name="gaussian_camera",
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=['panda_link0', 'panda_link1', 'panda_link2'],
    cache_background=True,  # 静态相机启用缓存 (81× 加速)
    return_components=True,
)

# 2. 创建环境 (4096 个并行环境)
env = Environment(
    model_path="franka_kitchen.xml",
    sensors=[cfg.build()],
    num_envs=4096,
    device="cuda"
)

# 3. 训练循环
obs = env.reset()
for step in range(1_000_000):
    # obs['gaussian_camera'].rgb: (4096, 480, 640, 3) torch.Tensor
    action = policy(obs['gaussian_camera'].rgb)
    obs, reward, done, info = env.step(action)
```

**适用场景**: RL 训练、大规模仿真、性能优化

---

## 🎨 渲染模式

### Mode 1: Hybrid (混合) ✅ 推荐

```python
sensor = GaussianSensor(
    render_mode="hybrid",
    background_ply_path="scene.ply",  # 必需
    robot_geom_names=['link1', 'link2'],  # 必需
)
```

**效果**: 
- 背景 = 3DGS (照片级真实感)
- 前景 = MuJoCo (物理准确机器人)
- 合成 = `bg * (1-mask) + fg * mask`

**性能**: ~17ms/帧 (单环境)

---

### Mode 2: 3DGS Only (纯背景)

```python
sensor = GaussianSensor(
    render_mode="3dgs_only",
    background_ply_path="scene.ply",  # 必需
)
```

**效果**: 只渲染 3DGS 背景  
**性能**: ~15ms/帧  
**用途**: 静态场景可视化

---

### Mode 3: MuJoCo Only (纯前景)

```python
sensor = GaussianSensor(
    render_mode="mujoco_only",
)
```

**效果**: 标准 MuJoCo 渲染  
**性能**: ~2ms/帧  
**用途**: 调试、对比实验

---

## 📐 关键参数

### GaussianSensor 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width` | int | 640 | 图像宽度 |
| `height` | int | 480 | 图像高度 |
| `background_ply_path` | str | None | 3DGS 背景模型路径 |
| `render_mode` | str | "hybrid" | 渲染模式 |
| `robot_geom_names` | list[str] | [] | 机器人部件名称列表 |
| `fov_degrees` | float | 60.0 | 相机视场角 |

### GaussianSensorMjlabCfg 参数 (批量模式)

```python
cfg = GaussianSensorMjlabCfg(
    name="camera_name",           # 传感器名称
    width=640,                     # 图像宽度
    height=480,                    # 图像高度
    
    # 相机配置 (二选一)
    camera_name="existing_cam",    # 选项1: 使用场景中已有的相机
    # 或
    pos=(0.8, -0.6, 1.0),         # 选项2: 创建新相机 - 位置
    quat=(1, 0, 0, 0),            # 四元数方向
    fov_degrees=60.0,             # 视场角
    
    # 渲染配置
    background_ply_path="scene.ply",
    render_mode="hybrid",
    robot_geom_names=['link1', 'link2'],
    
    # 性能优化
    cache_background=True,         # 静态相机缓存 (推荐)
    return_components=True,        # 返回各组件
)
```

---

## 💡 常见使用场景

### 场景 1: 单帧可视化

```python
import matplotlib.pyplot as plt
from mugs.sensors import GaussianSensor

# 渲染
sensor = GaussianSensor(width=640, height=480, render_mode="hybrid", ...)
result = sensor.render(model, data, "camera")

# 显示
plt.figure(figsize=(15, 5))
plt.subplot(131); plt.imshow(result['background']); plt.title('3DGS Background')
plt.subplot(132); plt.imshow(result['foreground']); plt.title('MuJoCo Foreground')
plt.subplot(133); plt.imshow(result['rgb']); plt.title('Hybrid Result')
plt.show()
```

---

### 场景 2: 视频序列生成

```python
import cv2

sensor = GaussianSensor(...)
video = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640, 480))

for step in range(360):  # 10 秒 @ 30 FPS
    # 更新物理
    mujoco.mj_step(model, data)
    
    # 渲染
    result = sensor.render(model, data, "camera")
    
    # 写入视频 (BGR 格式)
    video.write(cv2.cvtColor(result['rgb'], cv2.COLOR_RGB2BGR))

video.release()
```

---

### 场景 3: 数据集生成

```python
import h5py
import numpy as np

sensor = GaussianSensor(...)
dataset = h5py.File('dataset.h5', 'w')

# 预分配空间
N = 10000
dataset.create_dataset('observations', shape=(N, 480, 640, 3), dtype='uint8')
dataset.create_dataset('actions', shape=(N, 7), dtype='float32')

for i in range(N):
    # 随机动作
    action = np.random.randn(7)
    mujoco.mj_step(model, data)
    
    # 渲染观测
    obs = sensor.render(model, data, "camera")['rgb']
    
    # 存储
    dataset['observations'][i] = obs
    dataset['actions'][i] = action

dataset.close()
```

---

### 场景 4: RL 训练 (批量)

```python
import torch
from mjlab import Environment
from mugs.sensors import GaussianSensorMjlabCfg

# 创建环境
cfg = GaussianSensorMjlabCfg(name="rgb", width=224, height=224, ...)
env = Environment("scene.xml", sensors=[cfg.build()], num_envs=4096, device="cuda")

# 策略网络
policy = MyPolicy().to("cuda")
optimizer = torch.optim.Adam(policy.parameters())

# 训练
for epoch in range(100):
    obs = env.reset()
    episode_reward = 0
    
    for step in range(1000):
        # obs['rgb'].rgb: (4096, 224, 224, 3) torch.Tensor on cuda
        action = policy(obs['rgb'].rgb)
        obs, reward, done, info = env.step(action)
        
        # PPO 更新...
        loss = compute_loss(...)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        episode_reward += reward.mean()
```

---

## 🔧 高级用法

### 外部相机参数 (解决相机对齐)

```python
import json

# 加载预训练 3DGS 相机
with open("cameras.json") as f:
    cameras = json.load(f)
    pretrained_camera = cameras[100]  # 使用第 100 个相机

# 渲染时使用预训练相机
result = sensor.render(
    model, data, 
    camera_name="mujoco_camera",      # MuJoCo 用这个相机
    camera_params=pretrained_camera,  # 3DGS 用预训练相机
)
```

**用途**: 当 MuJoCo 相机和 3DGS 训练相机不匹配时

---

### 动态切换渲染模式

```python
sensor = GaussianSensor(render_mode="hybrid", ...)

# 运行时切换
sensor.cfg.render_mode = "mujoco_only"  # 切换到纯 MuJoCo
result = sensor.render(model, data, "camera")

sensor.cfg.render_mode = "hybrid"  # 切换回混合
result = sensor.render(model, data, "camera")
```

**注意**: 不推荐频繁切换，仅用于调试

---

### 获取机器人遮罩

```python
result = sensor.render(model, data, "camera", return_components=True)
mask = result['mask']  # (H, W, 1) float32, 范围 [0, 1]

# 二值化
binary_mask = (mask > 0.5).astype(np.uint8) * 255

# 统计机器人像素占比
robot_ratio = mask.mean()
print(f"Robot pixels: {robot_ratio*100:.2f}%")
```

---

## ⚡ 性能优化技巧

### 技巧 1: 启用背景缓存 (静态相机)

```python
cfg = GaussianSensorMjlabCfg(
    cache_background=True,  # ← 静态相机 81× 加速！
    ...
)
```

**前提**: 相机位置不变  
**效果**: 0ms 背景渲染 (第二帧起)

---

### 技巧 2: 降低分辨率

```python
# 训练用低分辨率
cfg = GaussianSensorMjlabCfg(width=224, height=224, ...)  # 4× faster

# 演示用高分辨率
cfg = GaussianSensorMjlabCfg(width=640, height=480, ...)
```

**规律**: 渲染时间 ∝ 像素数

---

### 技巧 3: 仅在需要时返回组件

```python
# 训练时 - 只要 RGB
cfg = GaussianSensorMjlabCfg(return_components=False, ...)
obs = env.step(action)[0]
rgb = obs['rgb'].rgb  # 只有最终 RGB

# 调试时 - 返回所有组件
cfg = GaussianSensorMjlabCfg(return_components=True, ...)
obs = env.step(action)[0]
bg = obs['rgb'].background
fg = obs['rgb'].foreground
mask = obs['rgb'].mask
```

---

## 🐛 常见问题

### Q1: 背景全黑？

**原因**: MuJoCo 相机和 3DGS 相机不匹配

**解决**:
```python
# 方案1: 使用外部相机参数
result = sensor.render(model, data, "cam", camera_params=pretrained_cam)

# 方案2: 调整 MuJoCo 相机到 3DGS 相机位置
# 在 XML 中修改 <camera pos="x y z" quat="w x y z"/>
```

---

### Q2: 机器人不可见？

**原因**: `robot_geom_names` 未正确配置

**解决**:
```python
# 查看模型中所有 geom 名称
for i in range(model.ngeom):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i)
    print(f"Geom {i}: {name}")

# 正确配置
sensor = GaussianSensor(
    robot_geom_names=['找到的实际名称1', '找到的实际名称2', ...],
    ...
)
```

---

### Q3: 渲染很慢？

**检查清单**:
- ✅ 使用 CUDA (`device="cuda"`)
- ✅ 批量模式而非循环 (`Environment` vs 手动 for 循环)
- ✅ 静态相机启用缓存 (`cache_background=True`)
- ✅ 合理分辨率 (640×480 或更低)

---

## 📚 完整示例

### 最小可运行示例

```python
"""
最简单的 MuGS 使用示例
需要: scene.xml, background.ply
"""

import mujoco
import numpy as np
from mugs.sensors import GaussianSensor

# 1. 加载场景
model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# 2. 创建传感器
sensor = GaussianSensor(
    width=640,
    height=480,
    background_ply_path="background.ply",
    render_mode="hybrid",
    robot_geom_names=['base_link'],  # 根据实际修改
)

# 3. 仿真 + 渲染
for i in range(100):
    # 物理步进
    mujoco.mj_step(model, data)
    
    # 渲染
    result = sensor.render(model, data, "camera_name")  # 根据实际修改
    
    # 使用结果
    rgb = result['rgb']  # (480, 640, 3) numpy array
    print(f"Frame {i}: shape={rgb.shape}, dtype={rgb.dtype}")
```

---

## 🎯 下一步

- 📖 阅读完整文档: `README.md`
- 🧪 运行示例: `python examples/gaussian_sensor_demo.py`
- 🔬 查看测试: `examples/test_*.py`
- 📊 性能数据: `docs/PROJECT_STATUS.md`

---

## 📞 支持

- 问题反馈: GitHub Issues
- 示例代码: `examples/` 目录
- 测试用例: `tests/` 目录

---

<p align="center">
  <b>MuGS API</b><br/>
  <i>5 分钟上手 | 照片级真实 | 大规模并行</i>
</p>
