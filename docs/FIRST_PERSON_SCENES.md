# 第一人称桌面操作场景建议

**需求**: 机器人第一视角 + 桌面物体 + 3DGS 混合渲染  
**目标**: 更真实的 VLA 训练场景

---

## 🎯 推荐场景方案

### 方案 1: RLBench 场景 + 3DGS 重建 ⭐ 推荐

**数据集**: [RLBench](https://github.com/stepjam/RLBench)

**特点**:
- ✅ 桌面操作任务（100+ 任务）
- ✅ 机器臂第一人称视角
- ✅ 多种物体和场景
- ✅ 已有 MuJoCo/PyRep 支持

**实施步骤**:

```bash
# 1. 安装 RLBench
pip install rlbench

# 2. 采集真实或仿真数据
python scripts/collect_rlbench_data.py \
    --task reach_target \
    --episodes 100 \
    --save-images

# 3. 3DGS 重建桌面场景
python scripts/train_3dgs.py \
    --images data/rlbench/reach_target/images \
    --output data/pretrained/rlbench_desk

# 4. 创建 MuJoCo 场景
# scenes/rlbench_desk.xml (相同布局)

# 5. 配置第一人称相机
cfg = GaussianSensorMjlabCfg(
    name="wrist_camera",  # 手腕相机
    camera_name="wrist_cam",  # 已挂载在机器人手腕
    background_ply_path="data/pretrained/rlbench_desk/point_cloud.ply",
    render_mode="hybrid",
)
```

**优势**:
- 任务明确（reach, grasp, pick and place）
- 已有大量研究使用
- 容易复现和对比

---

### 方案 2: ManiSkill2 场景 ⭐⭐

**数据集**: [ManiSkill2](https://github.com/haosulab/ManiSkill2)

**特点**:
- ✅ 真实感渲染
- ✅ 多种操作任务
- ✅ GPU 加速仿真
- ✅ 支持 Sapien/MuJoCo

**场景示例**:
- PickCube: 桌面抓取立方体
- StackCube: 堆叠任务
- PegInsertion: 插销任务
- TurnFaucet: 操作水龙头

**实施**:
```python
import mujoco
from mugs.sensors import GaussianSensor

# 1. 导出 ManiSkill2 场景到 MuJoCo
# (需要手动转换 URDF/MJCF)

# 2. 配置腕部相机
model = mujoco.MjModel.from_xml_path("maniskill2_pickcube.xml")
sensor = GaussianSensor(
    width=640, height=480,
    background_ply_path="data/maniskill2_desk.ply",
    render_mode="hybrid",
)

# 3. 第一人称渲染
rgb = sensor.render(model, data, camera_name="wrist_rgb")
```

---

### 方案 3: 使用现有 Kitchen 场景改造 ✅ 最快

**基于**: 当前的 kitchen.ply

**改造步骤**:

#### 1. 修改相机为第一人称

```xml
<!-- scenes/kitchen_first_person.xml -->
<mujoco model="kitchen_fp">
  <compiler angle="radian"/>
  
  <worldbody>
    <light pos="0 0 3" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="5 5 0.1"/>
    
    <!-- 机器人 -->
    <body name="robot_base" pos="0.5 0 0.9">  <!-- 桌面高度 -->
      <camera name="wrist_cam" 
              pos="0 0 0"           <!-- 相机在机器人手腕 -->
              euler="0 0 0"          <!-- 向前看 -->
              fovy="60"/>
      
      <!-- 简化的机械臂（可选，也可以完全隐藏） -->
      <geom name="gripper" type="box" size="0.02 0.05 0.02" 
            rgba="0.8 0.8 0.8 0.3" pos="0 0 -0.05"/>
    </body>
    
    <!-- 桌面物体 -->
    <body name="cup" pos="0 0.2 0.95">
      <geom name="cup_geom" type="cylinder" size="0.03 0.08" 
            rgba="0.8 0.2 0.2 1"/>
    </body>
    
    <body name="plate" pos="0 -0.2 0.9">
      <geom name="plate_geom" type="cylinder" size="0.08 0.01" 
            rgba="0.9 0.9 0.9 1"/>
    </body>
  </worldbody>
</mujoco>
```

#### 2. 配置传感器

```python
from mugs.sensors import GaussianSensor

sensor = GaussianSensor(
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=['gripper'],  # 只渲染夹爪（前景）
)

# 渲染
result = sensor.render(model, data, camera_name="wrist_cam")
```

**效果**:
- 背景: Kitchen 的真实厨房场景（3DGS）
- 前景: 桌面物体 + 部分夹爪（MuJoCo）
- 视角: 第一人称（手腕视角）

---

### 方案 4: 公开 3DGS 桌面数据集

#### 选项 A: Mip-NeRF 360 - Counter 场景

**下载**: [Counter Scene](https://jonbarron.info/mipnerf360/)

```bash
# 1. 下载
wget https://storage.googleapis.com/gresearch/refraw360/counter.zip
unzip counter.zip -d data/raw/counter

# 2. 训练 3DGS
python external/gaussian-splatting/train.py \
    -s data/raw/counter \
    -m data/pretrained/counter \
    --iterations 30000

# 3. 创建匹配的 MuJoCo 场景
# 在 counter 上放置物体
```

**特点**:
- ✅ 高质量桌面场景
- ✅ 已有 3DGS 预训练模型
- ✅ 多角度采集

#### 选项 B: Replica Dataset - Office 场景

**下载**: [Replica Dataset](https://github.com/facebookresearch/Replica-Dataset)

```bash
# 包含多个室内场景，包括办公桌
wget https://github.com/facebookresearch/Replica-Dataset/releases/download/v1.0/office_0.zip
```

---

## 🛠️ 实施指南

### Step 1: 创建第一人称 Kitchen 演示

```python
"""
first_person_kitchen_demo.py
使用现有 kitchen.ply，创建第一人称桌面操作演示
"""

import mujoco
import numpy as np
from mugs.sensors import GaussianSensor
import matplotlib.pyplot as plt

# 创建简单桌面场景
scene_xml = """
<mujoco model="fp_kitchen">
  <compiler angle="radian"/>
  <option timestep="0.002"/>
  
  <visual>
    <global offwidth="640" offheight="480"/>
  </visual>
  
  <worldbody>
    <light pos="2 0 3" dir="-1 0 -1"/>
    <geom name="floor" type="plane" size="5 5 0.1"/>
    
    <!-- 相机挂载点（模拟机器人手腕） -->
    <body name="wrist" pos="1.5 0 1.2" euler="0 0.3 0">
      <camera name="wrist_cam" pos="0 0 0" euler="0 0 0" fovy="60"/>
      
      <!-- 简化夹爪 -->
      <geom name="gripper_base" type="box" size="0.02 0.03 0.02" 
            rgba="0.3 0.3 0.3 0.5" pos="0 0 -0.05"/>
      <geom name="gripper_left" type="box" size="0.005 0.04 0.015" 
            rgba="0.5 0.5 0.5 0.5" pos="-0.03 0 -0.08"/>
      <geom name="gripper_right" type="box" size="0.005 0.04 0.015" 
            rgba="0.5 0.5 0.5 0.5" pos="0.03 0 -0.08"/>
    </body>
    
    <!-- 桌面物体 -->
    <body name="mug" pos="1.8 0.1 1.0">
      <joint type="free"/>
      <geom name="mug_geom" type="cylinder" size="0.035 0.08" 
            rgba="0.8 0.3 0.2 1" mass="0.2"/>
    </body>
    
    <body name="bowl" pos="2.0 -0.2 0.95">
      <joint type="free"/>
      <geom name="bowl_geom" type="cylinder" size="0.06 0.03" 
            rgba="0.2 0.6 0.8 1" mass="0.15"/>
    </body>
    
    <body name="plate" pos="1.6 0.3 0.9">
      <geom name="plate_geom" type="cylinder" size="0.09 0.01" 
            rgba="0.9 0.9 0.9 1"/>
    </body>
  </worldbody>
  
  <actuator>
    <!-- 可以添加夹爪控制 -->
  </actuator>
</mujoco>
"""

# 保存场景
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
    f.write(scene_xml)
    scene_path = f.name

# 加载
model = mujoco.MjModel.from_xml_path(scene_path)
data = mujoco.MjData(model)

# 创建传感器
sensor = GaussianSensor(
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=['gripper_base', 'gripper_left', 'gripper_right'],
)

# 渲染第一人称视角
result = sensor.render(
    model, data, 
    camera_name="wrist_cam",
    return_components=True,
)

# 显示
fig, axes = plt.subplots(1, 4, figsize=(20, 5))
axes[0].imshow(result['background'])
axes[0].set_title('3DGS Kitchen Background')
axes[1].imshow(result['foreground'])
axes[1].set_title('MuJoCo Objects + Gripper')
axes[2].imshow(result['mask'], cmap='gray')
axes[2].set_title('Robot Mask')
axes[3].imshow(result['rgb'])
axes[3].set_title('First-Person View')
plt.tight_layout()
plt.savefig('first_person_demo.jpg', dpi=150)
print("✅ Saved: first_person_demo.jpg")
```

---

### Step 2: 添加动态操作

```python
"""
添加夹爪运动和物体操作
"""

# 创建关键帧动画
keyframes = [
    # (wrist_pos, gripper_opening)
    ([1.5, 0.0, 1.2], 0.06),  # 初始位置，张开
    ([1.8, 0.1, 1.05], 0.06), # 接近杯子
    ([1.8, 0.1, 1.0], 0.02),  # 抓取杯子
    ([1.5, 0.0, 1.2], 0.02),  # 提起杯子
]

frames = []
for i, (pos, opening) in enumerate(keyframes):
    # 更新机器人位置
    data.qpos[0:3] = pos  # 假设前 3 个自由度是位置
    
    # 仿真
    mujoco.mj_forward(model, data)
    
    # 渲染
    result = sensor.render(model, data, "wrist_cam")
    frames.append(result['rgb'])
    
    # 保存关键帧
    plt.imsave(f'keyframe_{i}.jpg', result['rgb'])

print(f"✅ Generated {len(frames)} keyframes")
```

---

## 📊 场景对比

| 场景 | 真实感 | 任务明确 | 实施难度 | 数据可用 |
|------|--------|----------|----------|----------|
| **RLBench** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **ManiSkill2** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Kitchen 改造** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Counter 场景** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐**: 先用 **Kitchen 改造**（最快），再考虑 **RLBench**（最标准）

---

## 🎯 关键要点

### 第一人称视角配置

```xml
<!-- 正确的第一人称相机 -->
<camera name="wrist_cam" 
        pos="0 0 0"      <!-- 相对于 parent body -->
        euler="0 0 0"    <!-- 向前看 -->
        fovy="60"        <!-- 适中的 FOV -->
        mode="fixed"/>   <!-- 固定相机 -->
```

### 物体布局建议

```
相机视野内应包含:
- 2-5 个可操作物体
- 至少 1 个目标位置
- 部分机器人（夹爪/手腕）

避免:
- 物体太远（看不清）
- 物体太近（超出视野）
- 机器人遮挡过多
```

### 3DGS 背景要求

```
理想的桌面 3DGS 数据集:
- 分辨率: 1080p+
- 视角数: 100+ 张图像
- 覆盖范围: 桌面及周围环境
- 光照: 均匀，无强烈阴影变化
```

---

## 📦 数据集资源

### 已验证可用

1. **Mip-NeRF 360 - Kitchen**: ✅ 当前使用
2. **Mip-NeRF 360 - Counter**: ⏳ 推荐尝试

### 推荐采集

1. **自己拍摄桌面**: 
   - 手机/相机拍摄 100+ 张桌面照片
   - 使用 COLMAP + 3DGS 重建
   - 匹配 MuJoCo 场景布局

2. **使用 Isaac Sim**:
   - 渲染高质量合成数据
   - 自动相机标定
   - 完美 GT 对齐

---

## 🚀 快速启动

```bash
# 1. 创建第一人称演示（使用现有 kitchen）
cd /home/ununtu/metabot-workspace/mugs
python examples/first_person_kitchen_demo.py

# 2. 下载 Counter 场景（可选）
# wget https://storage.googleapis.com/gresearch/refraw360/counter.zip

# 3. 探索 RLBench（推荐）
# pip install rlbench
# python examples/rlbench_3dgs_demo.py
```

---

## 💡 为什么第一人称很重要？

1. **更真实的 VLA 训练**: 
   - 符合实际机器人视角
   - 减小 Sim2Real 差距

2. **更好的空间理解**:
   - 深度感知更准确
   - 手眼协调更自然

3. **任务聚焦**:
   - 关注操作目标
   - 减少无关信息

---

<p align="center">
  <b>第一人称场景</b><br/>
  <i>VLA 训练 | 真实视角 | 任务明确</i>
</p>
