# MuJoCo Segmentation ID Guide

## Segment ID机制

### MuJoCo如何生成Segmentation ID

MuJoCo的分割渲染会为每个像素分配一个**geom ID**，表示该像素属于哪个几何体。

```python
# 启用分割渲染
renderer.enable_segmentation_rendering()
seg = renderer.render()  # (H, W, 3) RGB格式，但实际是ID

# 提取geom ID（通常在R通道）
seg_ids = seg[:, :, 0].astype(np.int32)
```

### Segment ID含义

| ID值 | 含义 |
|------|------|
| **-1** | 背景（天空/void） |
| **0** | 第一个geom（通常是ground plane） |
| **1, 2, 3...** | 其他geom（按照XML定义顺序） |

### 示例场景

```xml
<worldbody>
    <geom name="ground" .../>        <!-- ID = 0 -->
    <geom name="table_top" .../>     <!-- ID = 1 -->
    <geom name="table_leg1" .../>    <!-- ID = 2 -->
    
    <body name="robot">
        <geom name="palm" .../>      <!-- ID = 6 -->
        <geom name="finger1" .../>   <!-- ID = 7 -->
        <geom name="finger2" .../>   <!-- ID = 8 -->
    </body>
</worldbody>
```

**实际渲染的unique IDs**: `[-1, 0, 1, 2, 6, 7, 8, 10, 11]`

注意：
- ID不一定连续（跳过了3, 4, 5, 9）
- 这是因为有些body没有geom，或者geom被group过滤掉

### 从Segment ID提取Mask

```python
def create_robot_mask(seg_ids: np.ndarray, model) -> np.ndarray:
    """提取机器人部件的二值mask"""
    
    # 1. 定义机器人geom名称
    robot_geom_names = [
        "palm", 
        "finger1_link", 
        "finger2_link",
        "finger3_link", 
        "finger4_link", 
        "finger5_link",
    ]
    
    # 2. 查询每个geom的ID
    robot_geom_ids = []
    for name in robot_geom_names:
        geom_id = mujoco.mj_name2id(
            model, 
            mujoco.mjtObj.mjOBJ_GEOM,  # 查询geom类型
            name
        )
        if geom_id >= 0:  # -1表示未找到
            robot_geom_ids.append(geom_id)
    
    # 3. 创建二值mask
    mask = np.zeros_like(seg_ids, dtype=np.uint8)
    for geom_id in robot_geom_ids:
        mask[seg_ids == geom_id] = 1  # 机器人=1，其他=0
    
    return mask
```

### 查询Geom ID的方法

```python
# 方法1: 通过名称查询
geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "palm")
print(f"Palm geom ID: {geom_id}")  # 例如: 6

# 方法2: 遍历所有geom
for i in range(model.ngeom):
    name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i)
    print(f"Geom {i}: {name}")

# 方法3: 从seg_ids分析
unique_ids = np.unique(seg_ids)
print(f"Visible geom IDs: {unique_ids}")
```

### 高级用法

#### 1. 分离不同类型的物体

```python
# 环境geom（桌子、地面）
env_geom_names = ["ground", "table_top", "table_leg1", ...]
env_geom_ids = [mujoco.mj_name2id(...) for name in env_geom_names]

# 机器人geom
robot_geom_ids = [...]

# 操作物体geom
object_geom_ids = [...]

# 创建不同的mask
env_mask = np.isin(seg_ids, env_geom_ids).astype(np.uint8)
robot_mask = np.isin(seg_ids, robot_geom_ids).astype(np.uint8)
object_mask = np.isin(seg_ids, object_geom_ids).astype(np.uint8)
```

#### 2. 多层合成

```python
# 3层合成：背景 + 3DGS物体 + MuJoCo机器人
background = np.ones((H, W, 3)) * 0.95  # 浅灰

# Layer 1: 3DGS渲染（环境+物体）
gs_render = render_3dgs(...)

# Layer 2: 只保留3DGS中的物体部分
object_only = np.where(object_mask[..., None], gs_render, background)

# Layer 3: 叠加机器人
final = np.where(robot_mask[..., None], mujoco_rgb, object_only)
```

#### 3. 调试：可视化所有geom

```python
# 为每个geom ID分配不同颜色
cmap = plt.cm.get_cmap('tab20')
colored_seg = np.zeros((H, W, 3))

for i, geom_id in enumerate(np.unique(seg_ids)):
    if geom_id == -1:
        continue  # 跳过背景
    
    mask = (seg_ids == geom_id)
    color = cmap(i % 20)[:3]  # RGB
    colored_seg[mask] = color

plt.imshow(colored_seg)
plt.title("Segmentation Visualization")
```

### 注意事项

1. **Geom ID != Body ID**
   - Body可以包含多个geom
   - 需要查询geom而非body

2. **Group过滤**
   ```xml
   <geom name="invisible" group="2" .../>  <!-- 可能不渲染 -->
   ```
   - `group="0"` 默认渲染
   - `group="1,2,3,4"` 可选择性渲染

3. **动态场景**
   - Geom ID不会改变（即使物体移动）
   - 只有添加/删除geom时ID才变化

4. **性能**
   - 分割渲染比RGB渲染慢（需要额外pass）
   - 只在需要mask时才启用

### 常见问题

**Q: 为什么unique IDs不连续？**
A: 有些geom可能：
- 在其他group中（不渲染）
- 在相机视野外
- 被其他物体遮挡

**Q: Robot mask全空（0%）怎么办？**
A: 检查：
1. 机器人是否在相机视野内
2. Geom名称是否正确
3. 机器人geom是否在正确的group

**Q: 如何确认geom是否可见？**
```python
seg_ids = render_segmentation(...)
unique_ids = np.unique(seg_ids)

for name in robot_geom_names:
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    if geom_id in unique_ids:
        print(f"✅ {name} visible (ID={geom_id})")
    else:
        print(f"❌ {name} not visible (ID={geom_id})")
```

### 混合渲染中的应用

```python
# 完整流程
def hybrid_render(model, data, gaussians, camera):
    # 1. MuJoCo渲染（机器人+环境）
    mujoco_rgb = render_rgb(model, data, camera)
    
    # 2. 分割mask
    seg_ids = render_segmentation(model, data, camera)
    
    # 3. 提取机器人mask
    robot_mask = create_robot_mask(seg_ids, model)
    
    # 4. 3DGS渲染（只有环境+物体，不包括机器人）
    gs_rgb = render_3dgs(gaussians, camera)
    
    # 5. 合成
    # 机器人区域用MuJoCo，其他区域用3DGS
    mask_3ch = robot_mask[..., None].repeat(3, axis=-1)
    composite = np.where(mask_3ch, mujoco_rgb, gs_rgb)
    
    return composite
```

---

**参考**:
- MuJoCo文档: https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#rendering
- 示例代码: `examples/phase1/hybrid_rendering_fixed.py`
