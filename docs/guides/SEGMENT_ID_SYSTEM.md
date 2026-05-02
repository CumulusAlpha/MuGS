# MuJoCo Segmentation ID系统详解

## 📋 概述

本文档详细说明MuGS如何从MuJoCo获取segmentation ID，并使用segment ID实现灵活的混合渲染掩码系统。

**核心概念**:
- MuJoCo可以渲染**segmentation map**，每个像素的值对应该像素所属的**geom ID**
- 通过segment ID，我们可以精确识别图像中的每个几何体
- 基于segment ID创建mask，实现MuJoCo与3DGS的混合渲染
- 使用YAML配置文件灵活控制哪些物体用MuJoCo渲染，哪些用3DGS

---

## 🎯 Segmentation ID基础

### MuJoCo的Segmentation渲染

MuJoCo提供专门的segmentation渲染模式，每个像素输出对应geom的ID：

```python
import mujoco

# 创建渲染器（启用segmentation）
renderer = mujoco.Renderer(
    model,
    height=480,
    width=640,
    enable_segmentation=True  # 关键！
)

# 更新场景
renderer.update_scene(data, camera="camera_name")

# 渲染segmentation map
seg_ids = renderer.render()  # 默认返回segmentation
# 或显式指定
seg_ids = renderer.segmentation  # (480, 640) int32 array

# 每个像素的值 = 该像素对应的geom ID
# 值范围：-1（背景/无几何体）, 0 ~ model.ngeom-1
```

### Segmentation Map示例

```
场景：一个桌子上有机器人手臂和杯子

Segmentation Map (5x5示例):
[[-1, -1, -1, -1, -1],    # -1 = 背景（天空）
 [-1,  3,  3,  3, -1],    #  3 = 桌面geom
 [ 8,  8,  3,  3, 12],    #  8 = 机器人link1, 12 = 杯子
 [ 8,  9,  9, 12, 12],    #  9 = 机器人link2
 [ 9,  9, 10, 10, 10]]    # 10 = 机器人gripper
```

---

## 🔧 获取Segmentation ID的方法

### 方法1: 使用Renderer API（推荐）

**适用于**: MuGS_mjlab的GaussianSensor

```python
import mujoco

def render_mujoco_segmentation(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    camera_name: str,
    width: int,
    height: int,
    renderer: Optional[mujoco.Renderer] = None
) -> np.ndarray:
    """
    渲染MuJoCo segmentation map
    
    Returns:
        seg_ids: (H, W) int32 array, 每个像素的geom ID
    """
    # 创建或复用renderer
    if renderer is None:
        renderer = mujoco.Renderer(
            model,
            height=height,
            width=width,
            enable_segmentation=True
        )
    
    # 更新场景
    renderer.update_scene(data, camera=camera_name)
    
    # 获取segmentation
    seg_ids = renderer.segmentation.copy()  # (H, W) int32
    
    return seg_ids
```

### 方法2: 批量渲染（MJLab环境）

**适用于**: 多环境并行渲染

```python
def render_batch_segmentation(
    model: mujoco.MjModel,
    data_batch: List[mujoco.MjData],
    camera_name: str,
    width: int,
    height: int
) -> np.ndarray:
    """
    批量渲染segmentation（多环境）
    
    Returns:
        seg_batch: (N_env, H, W) int32 array
    """
    n_env = len(data_batch)
    seg_batch = np.empty((n_env, height, width), dtype=np.int32)
    
    # 为每个环境创建renderer（或使用共享renderer池）
    renderer = mujoco.Renderer(
        model, height=height, width=width,
        enable_segmentation=True
    )
    
    for i, data in enumerate(data_batch):
        renderer.update_scene(data, camera=camera_name)
        seg_batch[i] = renderer.segmentation.copy()
    
    return seg_batch
```

---

## 🎨 从Segment ID创建Mask

### 基础掩码提取

```python
def create_simple_mask(
    seg_ids: np.ndarray,
    target_geom_ids: List[int]
) -> np.ndarray:
    """
    为指定的geom IDs创建二值掩码
    
    Args:
        seg_ids: (H, W) segmentation map
        target_geom_ids: 要mask的geom ID列表
        
    Returns:
        mask: (H, W) uint8, 1=目标geom, 0=其他
    """
    mask = np.zeros_like(seg_ids, dtype=np.uint8)
    
    for geom_id in target_geom_ids:
        mask[seg_ids == geom_id] = 1
    
    return mask
```

**示例**:
```python
# 获取segmentation
seg_ids = render_mujoco_segmentation(model, data, "camera1", 640, 480)

# 创建机器人mask（假设机器人的geom IDs是 5,6,7,8,9）
robot_geom_ids = [5, 6, 7, 8, 9]
robot_mask = create_simple_mask(seg_ids, robot_geom_ids)

# robot_mask[i,j] = 1 → 该像素是机器人
# robot_mask[i,j] = 0 → 该像素不是机器人
```

---

## 📝 配置化Mask系统

### YAML配置格式

我们使用YAML配置文件定义mask规则，而不是硬编码geom ID：

```yaml
# assets/configs/mask_config_kitchen.yaml

# 默认背景：未被group覆盖的区域用什么渲染
default_background: "3dgs"

# 定义多个mask groups
groups:
  # Group 1: 机器人（用MuJoCo渲染）
  - name: robot
    # 方式1：显式列举geom名称
    geom_names:
      - palm
      - finger1_link
      - finger2_link
      - wrist_link
    rendering_mode: mujoco
    composite_priority: 10  # 数字越大，渲染在越上层
    
  # Group 2: 桌子（用MuJoCo渲染）  
  - name: table
    # 方式2：通过body名称（包含该body下所有geoms）
    body_names:
      - table_body
    rendering_mode: mujoco
    composite_priority: 1
    
  # Group 3: 桌面物体（用3DGS渲染）
  - name: objects
    # 方式3：通过名称前缀匹配
    geom_prefix: "obj_"  # 匹配 obj_mug, obj_plate, etc.
    rendering_mode: 3dgs
    composite_priority: 5
    
  # Group 4: 地面（用MuJoCo渲染）
  - name: floor
    geom_names:
      - floor
    rendering_mode: mujoco
    composite_priority: 0
```

### 配置解析流程

```python
from mugs.utils import MaskConfig

# 1. 加载配置
config = MaskConfig.from_yaml("assets/configs/mask_config_kitchen.yaml")

# config.groups: List[MaskGroup]
# config.default_background: "3dgs" or "mujoco"

# 2. 将配置转换为实际的geom IDs
from mugs.utils import resolve_geom_ids

for group in config.groups:
    geom_ids = resolve_geom_ids(model, group)
    print(f"{group.name}: geom IDs = {geom_ids}")

# 输出示例:
# robot: geom IDs = [5, 6, 7, 8, 9]
# table: geom IDs = [3]
# objects: geom IDs = [12, 13, 14]
# floor: geom IDs = [0]
```

### `resolve_geom_ids()` 实现原理

```python
def resolve_geom_ids(
    model: mujoco.MjModel,
    mask_group: MaskGroup
) -> List[int]:
    """
    将MaskGroup配置转换为实际的geom IDs
    
    支持三种选择方式:
    1. geom_names: 显式列举geom名称
    2. body_names: 选择body下的所有geoms
    3. geom_prefix: 前缀匹配
    """
    geom_ids = []
    
    # 方式1: 显式geom名称
    for geom_name in mask_group.geom_names:
        geom_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_GEOM,
            geom_name
        )
        if geom_id >= 0:
            geom_ids.append(geom_id)
    
    # 方式2: body名称（查找该body下所有geoms）
    for body_name in mask_group.body_names:
        body_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_BODY,
            body_name
        )
        if body_id >= 0:
            # 遍历所有geoms，找到属于这个body的
            for geom_id in range(model.ngeom):
                if model.geom_bodyid[geom_id] == body_id:
                    geom_ids.append(geom_id)
    
    # 方式3: 前缀匹配
    if mask_group.geom_prefix:
        for geom_id in range(model.ngeom):
            geom_name = mujoco.mj_id2name(
                model,
                mujoco.mjtObj.mjOBJ_GEOM,
                geom_id
            )
            if geom_name and geom_name.startswith(mask_group.geom_prefix):
                geom_ids.append(geom_id)
    
    return sorted(set(geom_ids))  # 去重并排序
```

---

## 🖼️ 混合渲染Pipeline

### 完整流程

```python
from mugs.utils import (
    MaskConfig,
    create_group_masks,
    composite_with_groups
)
from mugs.rendering import render_mujoco_rgb, render_mujoco_segmentation

# Step 1: 渲染MuJoCo RGB和Segmentation
mujoco_rgb = render_mujoco_rgb(
    model, data, camera_name, width, height
)  # (H, W, 3)

seg_ids = render_mujoco_segmentation(
    model, data, camera_name, width, height
)  # (H, W) int32

# Step 2: 渲染3DGS场景
from mugs import GaussianRenderer

gs_renderer = GaussianRenderer()
gs_rgb = gs_renderer.render(gaussians, camera)  # (H, W, 3)

# Step 3: 加载mask配置
config = MaskConfig.from_yaml("mask_config_kitchen.yaml")

# Step 4: 创建所有group的masks
group_masks = create_group_masks(seg_ids, model, config)
# group_masks = {
#     "robot": (H, W) uint8 mask,
#     "table": (H, W) uint8 mask,
#     "objects": (H, W) uint8 mask,
#     "floor": (H, W) uint8 mask
# }

# Step 5: 按优先级混合渲染
final_rgb = composite_with_groups(
    mujoco_rgb,
    gs_rgb,
    group_masks,
    config
)  # (H, W, 3)

# final_rgb 就是最终的混合渲染结果
```

### `composite_with_groups()` 实现

```python
def composite_with_groups(
    mujoco_rgb: np.ndarray,
    gs_rgb: np.ndarray,
    group_masks: Dict[str, np.ndarray],
    config: MaskConfig
) -> np.ndarray:
    """
    按配置的优先级混合多个渲染源
    
    Args:
        mujoco_rgb: (H, W, 3) MuJoCo渲染
        gs_rgb: (H, W, 3) 3DGS渲染
        group_masks: {group_name: (H, W) mask}
        config: Mask配置
        
    Returns:
        composite: (H, W, 3) 混合结果
    """
    # 1. 从默认背景开始
    if config.default_background == "3dgs":
        composite = gs_rgb.copy()
    else:
        composite = mujoco_rgb.copy()
    
    # 2. 按优先级排序（低→高）
    sorted_groups = sorted(
        config.groups,
        key=lambda g: g.composite_priority
    )
    
    # 3. 逐层叠加
    for group in sorted_groups:
        if group.name not in group_masks:
            continue
        
        mask = group_masks[group.name]
        mask_3ch = mask[..., None].astype(np.float32)  # (H, W, 1)
        
        # 选择渲染源
        if group.rendering_mode == "mujoco":
            source = mujoco_rgb
        elif group.rendering_mode == "3dgs":
            source = gs_rgb
        elif group.rendering_mode == "both":
            source = (mujoco_rgb + gs_rgb) / 2  # 平均
        else:
            continue
        
        # Alpha blending
        composite = composite * (1 - mask_3ch) + source * mask_3ch
    
    return composite
```

### 渲染优先级示例

配置:
```yaml
groups:
  - name: floor
    composite_priority: 0
  - name: table
    composite_priority: 1
  - name: objects
    composite_priority: 5
  - name: robot
    composite_priority: 10
```

渲染顺序（从下到上）:
```
Background (3DGS kitchen environment)
    ↑
Floor (MuJoCo, priority=0)
    ↑
Table (MuJoCo, priority=1)
    ↑
Objects (3DGS, priority=5) ← 杯子、盘子等用3DGS渲染
    ↑
Robot (MuJoCo, priority=10) ← 最上层，确保机器人不被遮挡
```

---

## 🚀 在GaussianSensor中的集成

### GaussianSensor完整实现

```python
from mugs import GaussianRenderer
from mugs.utils import MaskConfig, create_group_masks, composite_with_groups

class GaussianSensor:
    """
    MJLab的3DGS混合渲染传感器
    """
    
    def __init__(
        self,
        cfg: GaussianSensorCfg,
        model: mujoco.MjModel,
        data: mujoco.MjData
    ):
        self.cfg = cfg
        self.model = model
        self.data = data
        
        # 创建MuJoCo renderer（启用segmentation）
        self.mj_renderer = mujoco.Renderer(
            model,
            height=cfg.resolution[1],
            width=cfg.resolution[0],
            enable_segmentation=True  # 关键！
        )
        
        # 创建3DGS renderer
        self.gs_renderer = GaussianRenderer(device=cfg.device)
        
        # 加载3DGS场景
        from mugs.utils import load_ply_gaussians
        self.gaussians = load_ply_gaussians(cfg.scene_ply)
        
        # 加载mask配置
        self.mask_config = MaskConfig.from_yaml(cfg.mask_config)
    
    def update(self) -> np.ndarray:
        """
        渲染一帧（混合MuJoCo + 3DGS）
        
        Returns:
            rgb: (H, W, 3) uint8 混合渲染结果
        """
        # 1. 渲染MuJoCo RGB
        self.mj_renderer.update_scene(self.data, camera=self.cfg.camera_name)
        mujoco_rgb = self.mj_renderer.render()
        
        # 2. 获取segmentation
        seg_ids = self.mj_renderer.segmentation.copy()
        
        # 3. 提取相机参数并渲染3DGS
        from mugs_mjlab.utils import extract_mujoco_camera_params
        camera = extract_mujoco_camera_params(
            self.model,
            self.data,
            self.cfg.camera_name,
            self.cfg.resolution[0],
            self.cfg.resolution[1]
        )
        
        # 同步动态物体位姿（如果有）
        if self.cfg.dynamic_objects:
            from mugs_mjlab.utils import sync_physics_to_gaussians
            sync_physics_to_gaussians(
                self.gaussians,
                self.model,
                self.data,
                self.cfg.dynamic_objects
            )
        
        gs_rgb = self.gs_renderer.render(self.gaussians, camera)
        
        # 4. 创建masks
        group_masks = create_group_masks(
            seg_ids,
            self.model,
            self.mask_config
        )
        
        # 5. 混合渲染
        final_rgb = composite_with_groups(
            mujoco_rgb,
            gs_rgb,
            group_masks,
            self.mask_config
        )
        
        return final_rgb
```

---

## 📊 性能优化

### 优化1: 缓存Geom ID映射

```python
class GaussianSensor:
    def __init__(self, ...):
        # ...
        
        # 预先计算所有group的geom IDs（避免每帧resolve）
        self._group_geom_ids = {}
        for group in self.mask_config.groups:
            self._group_geom_ids[group.name] = resolve_geom_ids(
                self.model, group
            )
    
    def update(self):
        # ...
        
        # 直接使用缓存的geom IDs创建masks
        group_masks = self._create_masks_fast(seg_ids)
    
    def _create_masks_fast(self, seg_ids):
        masks = {}
        for group_name, geom_ids in self._group_geom_ids.items():
            mask = np.zeros_like(seg_ids, dtype=np.uint8)
            for gid in geom_ids:
                mask[seg_ids == gid] = 1
            masks[group_name] = mask
        return masks
```

### 优化2: GPU加速Mask创建

```python
import torch

def create_masks_gpu(
    seg_ids: torch.Tensor,  # (H, W) int32 on GPU
    group_geom_ids: Dict[str, List[int]],
    device: str = "cuda"
) -> Dict[str, torch.Tensor]:
    """
    GPU加速的mask创建
    
    Args:
        seg_ids: (H, W) segmentation tensor on GPU
        group_geom_ids: {group_name: [geom_ids]}
        
    Returns:
        {group_name: (H, W) bool mask on GPU}
    """
    masks = {}
    
    for group_name, geom_ids in group_geom_ids.items():
        # 创建所有geom ID的tensor
        gids_tensor = torch.tensor(geom_ids, device=device, dtype=torch.int32)
        
        # 向量化mask创建
        mask = torch.zeros_like(seg_ids, dtype=torch.bool)
        for gid in gids_tensor:
            mask |= (seg_ids == gid)
        
        masks[group_name] = mask
    
    return masks
```

### 优化3: 批量并行处理

```python
def update_batch(
    self,
    data_batch: List[mujoco.MjData],
    num_envs: int
) -> torch.Tensor:
    """
    批量渲染多个环境（GPU并行）
    
    Returns:
        rgb_batch: (N_env, H, W, 3) tensor
    """
    H, W = self.cfg.resolution[1], self.cfg.resolution[0]
    
    # 批量渲染MuJoCo（CPU，串行）
    mj_rgb_batch = []
    seg_batch = []
    for data in data_batch:
        self.mj_renderer.update_scene(data, camera=self.cfg.camera_name)
        mj_rgb_batch.append(self.mj_renderer.render())
        seg_batch.append(self.mj_renderer.segmentation.copy())
    
    # 转GPU
    mj_rgb_batch = torch.tensor(mj_rgb_batch, device="cuda")  # (N, H, W, 3)
    seg_batch = torch.tensor(seg_batch, device="cuda")  # (N, H, W)
    
    # 批量渲染3DGS（GPU并行）
    camera_batch = self._extract_camera_batch(data_batch)
    gs_rgb_batch = self.gs_renderer.render_batch(
        self.gaussians, camera_batch
    )  # (N, H, W, 3) on GPU
    
    # 批量创建masks和混合（GPU并行）
    final_batch = []
    for i in range(num_envs):
        masks = create_masks_gpu(seg_batch[i], self._group_geom_ids)
        final = composite_gpu(
            mj_rgb_batch[i],
            gs_rgb_batch[i],
            masks,
            self.mask_config
        )
        final_batch.append(final)
    
    return torch.stack(final_batch)  # (N, H, W, 3)
```

---

## 🧪 调试和验证

### 可视化Segmentation Map

```python
import matplotlib.pyplot as plt

def visualize_segmentation(seg_ids, model):
    """可视化segmentation map，不同geom用不同颜色"""
    # 创建颜色映射
    num_geoms = model.ngeom
    colors = plt.cm.tab20(np.linspace(0, 1, num_geoms))
    
    # 映射seg_ids到颜色
    H, W = seg_ids.shape
    vis = np.zeros((H, W, 3))
    for gid in range(num_geoms):
        mask = seg_ids == gid
        vis[mask] = colors[gid, :3]
    
    # 背景用黑色
    vis[seg_ids == -1] = [0, 0, 0]
    
    plt.imshow(vis)
    plt.title("Segmentation Visualization")
    plt.show()
```

### 验证Mask覆盖

```python
def verify_masks(group_masks, seg_ids):
    """检查masks是否有重叠或遗漏"""
    total_mask = np.zeros_like(seg_ids, dtype=np.uint8)
    
    for group_name, mask in group_masks.items():
        # 检查重叠
        overlap = (total_mask > 0) & (mask > 0)
        if overlap.any():
            print(f"⚠️  Warning: {group_name} overlaps with previous groups")
        
        total_mask += mask
    
    # 检查是否所有非背景像素都被覆盖
    non_background = seg_ids >= 0
    uncovered = non_background & (total_mask == 0)
    
    if uncovered.any():
        print(f"⚠️  Warning: {uncovered.sum()} pixels not covered by any group")
    else:
        print("✅ All pixels covered")
```

---

## 📚 参考示例

### 完整使用示例

见 `examples/mugs_mjlab/segment_id_demo.py`:

```python
from mugs_mjlab import GaussianSensor, GaussianSensorCfg
from mugs.utils import MaskConfig

# 1. 配置sensor
sensor_cfg = GaussianSensorCfg(
    camera_name="camera1",
    resolution=(640, 480),
    scene_ply="assets/scenes/kitchen.ply",
    mask_config="assets/configs/mask_config_kitchen.yaml",
    device="cuda"
)

# 2. 创建sensor
sensor = GaussianSensor(sensor_cfg, model, data)

# 3. 渲染
rgb = sensor.update()  # (480, 640, 3)

# 4. 可视化
import matplotlib.pyplot as plt
plt.imshow(rgb)
plt.title("Hybrid Rendering (MuJoCo + 3DGS)")
plt.show()
```

---

## 📌 总结

**Segment ID系统的核心优势**:
1. ✅ **精确控制**: 像素级别的渲染源选择
2. ✅ **灵活配置**: YAML配置，无需修改代码
3. ✅ **高性能**: 缓存优化 + GPU加速
4. ✅ **易于调试**: 可视化工具验证配置

**关键API**:
- `render_mujoco_segmentation()` - 获取segment ID
- `MaskConfig.from_yaml()` - 加载配置
- `resolve_geom_ids()` - 配置→geom IDs
- `create_group_masks()` - segment ID→masks
- `composite_with_groups()` - 混合渲染

**配置文件位置**:
- `assets/configs/mask_config_*.yaml`

---

**文档版本**: v1.0  
**最后更新**: 2026-05-02  
**维护者**: MuGS Team
