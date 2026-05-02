# MuJoCo与3DGS坐标对齐指南

## 坐标系统对比

### MuJoCo坐标系
- **右手坐标系**
- **+X**: 右
- **+Y**: 前
- **+Z**: 上（重力方向为-Z）
- **旋转**: 四元数(w, x, y, z)或欧拉角

### 3D Gaussian Splatting (OpenGL)坐标系
- **右手坐标系**
- **+X**: 右
- **+Y**: 上
- **+Z**: 后（相机朝向-Z）
- **旋转**: 四元数(w, x, y, z)

### 关键差异

| 特性 | MuJoCo | 3DGS/OpenGL |
|------|--------|-------------|
| 上方向 | +Z | +Y |
| 前方向 | +Y | -Z |
| 相机朝向 | 沿-Z（相机空间） | 沿-Z（相机空间） |
| 世界坐标 | Z-up | Y-up |

---

## 场景对齐策略

### 方案A: 统一使用MuJoCo坐标系（推荐）

**原理**: 3DGS场景在创建时就使用MuJoCo坐标系（Z-up）

**优点**:
- 无需运行时转换
- 物理仿真和渲染坐标一致
- 简单直观

**实现**:
```python
# 创建3DGS场景时，直接使用MuJoCo坐标
# 示例：在MuJoCo中放置一个杯子
mug_pos_mujoco = np.array([0.5, 0.0, 0.8])  # (x, y, z) in MuJoCo

# 3DGS中的杯子高斯应该使用相同坐标
mug_gaussians['means'] = ...  # 中心在(0.5, 0.0, 0.8)

# 渲染时，相机参数直接从MuJoCo提取
camera_pos = data.cam_xpos[camera_id]  # MuJoCo世界坐标
camera_mat = data.cam_xmat[camera_id]  # MuJoCo旋转矩阵
```

**注意**: 如果3DGS资产来自外部（如Mip-NeRF 360），需要预处理转换坐标系。

---

### 方案B: 运行时坐标转换

**原理**: 3DGS保持Y-up（OpenGL），运行时转换

**转换矩阵**:
```python
def mujoco_to_opengl_transform():
    """MuJoCo (Z-up) → OpenGL (Y-up) 变换矩阵"""
    # 绕X轴旋转-90度
    return np.array([
        [1,  0,  0,  0],
        [0,  0,  1,  0],
        [0, -1,  0,  0],
        [0,  0,  0,  1]
    ])

def transform_gaussians(gaussians, T):
    """应用变换到高斯参数"""
    # 变换位置
    means_hom = np.concatenate([
        gaussians['means'],
        np.ones((len(gaussians['means']), 1))
    ], axis=1)
    gaussians['means'] = (T @ means_hom.T).T[:, :3]
    
    # 变换四元数
    R = T[:3, :3]
    gaussians['quats'] = transform_quaternions(gaussians['quats'], R)
    
    return gaussians
```

**缺点**:
- 每帧需要转换（性能开销）
- 增加代码复杂度

---

## 相机对齐

### 从MuJoCo提取相机参数

```python
def extract_camera_params(model, data, camera_name):
    """从MuJoCo提取相机参数（已在MuJoCo坐标系）"""
    camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)
    
    # 位置（世界坐标）
    camera_pos = data.cam_xpos[camera_id].copy()
    
    # 方向（旋转矩阵）
    camera_mat = data.cam_xmat[camera_id].reshape(3, 3).copy()
    
    # MuJoCo相机坐标系: +X右, +Y下, +Z前
    # 转换到OpenGL/3DGS: +X右, +Y上, +Z后
    camera_forward = -camera_mat[:, 2]  # MuJoCo的+Z → OpenGL的-Z
    camera_up = -camera_mat[:, 1]       # MuJoCo的+Y(下) → OpenGL的-Y(-Y=上)
    camera_lookat = camera_pos + camera_forward
    
    # FOV
    fov = model.cam_fovy[camera_id]
    
    return {
        'position': camera_pos,
        'lookat': camera_lookat,
        'up': camera_up,
        'fov': fov
    }
```

### 视图矩阵构建

```python
def build_view_matrix(camera_pos, camera_lookat, camera_up):
    """构建OpenGL视图矩阵（兼容MuJoCo坐标）"""
    # 相机坐标系基向量
    z_axis = camera_pos - camera_lookat
    z_axis = z_axis / np.linalg.norm(z_axis)
    
    x_axis = np.cross(camera_up, z_axis)
    x_axis = x_axis / np.linalg.norm(x_axis)
    
    y_axis = np.cross(z_axis, x_axis)
    
    # 视图矩阵（世界→相机）
    view_matrix = np.eye(4)
    view_matrix[:3, 0] = x_axis
    view_matrix[:3, 1] = y_axis
    view_matrix[:3, 2] = z_axis
    view_matrix[:3, 3] = camera_pos
    
    # OpenGL expects inverse
    view_matrix = np.linalg.inv(view_matrix)
    
    return view_matrix
```

---

## 物体放置对齐

### 场景1: 手工放置物体

```python
# 在MuJoCo XML中定义物体位置
"""
<body name="mug" pos="0.5 0.0 0.8">
    <geom type="mesh" mesh="mug_mesh"/>
</body>
"""

# 3DGS高斯中心应匹配
mug_gaussians = load_ply('mug.ply')
mug_gaussians['means'] += np.array([0.5, 0.0, 0.8])  # 平移到MuJoCo位置

# 如果需要旋转
mug_quat_mujoco = np.array([1, 0, 0, 0])  # (w, x, y, z)
mug_gaussians['quats'] = apply_rotation(mug_gaussians['quats'], mug_quat_mujoco)
```

### 场景2: 动态物体（物理仿真）

```python
# 每帧更新3DGS物体位置
def update_object_gaussians(gaussians_dict, model, data):
    """同步MuJoCo物理状态到3DGS"""
    
    for obj_name, gaussians in gaussians_dict.items():
        # 获取MuJoCo中物体的当前pose
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, obj_name)
        
        pos = data.xpos[body_id]  # 位置
        quat = data.xquat[body_id]  # 四元数(w, x, y, z)
        
        # 更新高斯位置（相对于物体中心）
        gaussians['means'] = rotate_and_translate(
            gaussians['means_local'],  # 物体局部坐标
            quat,
            pos
        )
        
        # 更新高斯方向
        gaussians['quats'] = compose_quaternions(
            gaussians['quats_local'],
            quat
        )
    
    return gaussians_dict
```

---

## 多物体场景管理

### 配置文件示例

```yaml
# assets/scenes/kitchen_layout.yaml

scene:
  coordinate_system: "mujoco"  # or "opengl"
  
objects:
  - name: "coffee_mug"
    ply_file: "coffee_mug.ply"
    mujoco_body: "mug_body"
    position: [0.5, 0.0, 0.8]
    rotation: [1.0, 0.0, 0.0, 0.0]  # quat (w, x, y, z)
    rendering: "3dgs"
    
  - name: "table"
    ply_file: "kitchen_table.ply"
    mujoco_body: null  # Static, no physics
    position: [0.0, 0.0, 0.0]
    rotation: [1.0, 0.0, 0.0, 0.0]
    rendering: "both"  # Composite MuJoCo + 3DGS
    
  - name: "robot_gripper"
    mujoco_body: "robot_hand"
    rendering: "mujoco"  # Only MuJoCo (no 3DGS)
```

### 加载和对齐

```python
def load_scene_with_alignment(config_path):
    """加载场景并自动对齐坐标"""
    import yaml
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    coordinate_system = config['scene']['coordinate_system']
    
    gaussians_dict = {}
    
    for obj_config in config['objects']:
        if obj_config.get('ply_file'):
            # 加载PLY
            gaussians = load_ply(obj_config['ply_file'])
            
            # 应用位置和旋转
            pos = np.array(obj_config['position'])
            quat = np.array(obj_config['rotation'])
            
            gaussians['means'] = rotate_points(gaussians['means'], quat) + pos
            gaussians['quats'] = compose_quaternions(gaussians['quats'], quat)
            
            # 坐标系转换（如果需要）
            if coordinate_system == 'opengl':
                gaussians = transform_to_opengl(gaussians)
            
            gaussians_dict[obj_config['name']] = gaussians
    
    return gaussians_dict, config
```

---

## 验证对齐

### 可视化检查

```python
def verify_alignment(model, data, gaussians_dict, camera_name):
    """验证MuJoCo和3DGS是否对齐"""
    
    # 1. 渲染MuJoCo（带物体边界框）
    mujoco_rgb = render_mujoco_with_bbox(model, data, camera_name)
    
    # 2. 渲染3DGS
    gs_rgb = render_3dgs(gaussians_dict, camera_name)
    
    # 3. 叠加显示
    overlay = 0.5 * mujoco_rgb + 0.5 * gs_rgb
    
    # 4. 检查关键点
    # 示例：杯子把手应该在相同位置
    mug_handle_pos_mj = get_mujoco_point(model, data, 'mug_handle')
    mug_handle_pos_gs = gaussians_dict['mug']['means'][handle_idx]
    
    error = np.linalg.norm(mug_handle_pos_mj - mug_handle_pos_gs)
    
    print(f"Alignment error: {error:.4f} m")
    
    if error > 0.01:  # 1cm threshold
        print("⚠️  Alignment issue detected!")
    else:
        print("✅ Alignment verified")
    
    return overlay
```

### 数值检查

```python
def check_coordinate_consistency(model, data, gaussians_dict):
    """检查坐标系一致性"""
    
    for obj_name, gaussians in gaussians_dict.items():
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, obj_name)
        
        # MuJoCo中心
        mj_center = data.xpos[body_id]
        
        # 3DGS中心（平均位置）
        gs_center = gaussians['means'].mean(axis=0)
        
        # 检查差异
        diff = np.linalg.norm(mj_center - gs_center)
        
        print(f"{obj_name}:")
        print(f"  MuJoCo: {mj_center}")
        print(f"  3DGS:   {gs_center}")
        print(f"  Error:  {diff:.4f} m")
```

---

## 常见问题

### Q1: 3DGS物体上下颠倒？

**原因**: 坐标系混淆（Y-up vs Z-up）

**解决**:
```python
# 检查并翻转Y-Z轴
gaussians['means'][:, [1, 2]] = gaussians['means'][:, [2, 1]]
gaussians['means'][:, 2] *= -1  # 如果需要
```

### Q2: 物体位置偏移？

**原因**: 物体中心定义不一致

**解决**:
```python
# 确保3DGS物体中心在原点
gaussians['means'] -= gaussians['means'].mean(axis=0)

# 然后应用MuJoCo位置
gaussians['means'] += mujoco_position
```

### Q3: 相机视角不匹配？

**原因**: up向量定义错误

**解决**:
```python
# 检查MuJoCo相机坐标系
camera_mat = data.cam_xmat[camera_id].reshape(3, 3)
print("Camera axes:")
print(f"  Right (+X): {camera_mat[:, 0]}")
print(f"  Down  (+Y): {camera_mat[:, 1]}")  # MuJoCo中+Y向下
print(f"  Forward (+Z): {camera_mat[:, 2]}")

# 确保up向量取反
camera_up = -camera_mat[:, 1]  # OpenGL需要向上
```

---

## 推荐工作流程

1. **统一坐标系**: 在项目开始时选择MuJoCo坐标系（Z-up）
2. **资产预处理**: 所有3DGS PLY转换到MuJoCo坐标
3. **配置管理**: 使用YAML记录物体位置/旋转
4. **自动对齐**: 脚本自动加载和对齐场景
5. **可视化验证**: 每次修改后检查对齐

---

**参考代码**: `src/mugs/utils/rendering.py:extract_mujoco_camera_params()`
