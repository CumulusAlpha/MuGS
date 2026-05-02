# Camera Alignment Fix for MuGS

## Problem
3DGS background was showing wrong viewpoint (distant vegetables instead of matching robot camera view).

## Root Causes

### 1. FOV Unit Handling
**Issue**: Code assumed `model.cam_fovy` returns degrees, but it actually returns radians when `<compiler angle="radian"/>` is used in XML.

**Impact**: FOV was off by ~57x, causing completely wrong focal length calculations.

**Fix** (`gaussian_sensor.py:280-284`):
```python
# Before (WRONG):
fov_y_degrees = model.cam_fovy[camera_id]
fov_y_radians = np.radians(fov_y_degrees)

# After (CORRECT):
fov_y_radians = model.cam_fovy[camera_id]  # Already in radians
```

### 2. Coordinate System Mismatch
**Issue**: MuJoCo uses +Z forward convention, but OpenGL/3DGS uses -Z forward.

**Impact**: Camera was looking in opposite Z direction, showing flipped scene.

**Fix** (`gaussian_sensor.py:336-338`):
```python
# Convert MuJoCo camera coords to OpenGL coords
R_cam = camera_params['rotation_matrix'].copy()
R_cam[:, 2] = -R_cam[:, 2]  # Flip Z axis for OpenGL convention
```

### 3. Scene XML FOV Values
**Issue**: Scene used `fovy="55"` with `<compiler angle="radian"/>`, meaning 55 radians (~3151°).

**Fix**: Changed to correct radian values:
```xml
<!-- 55° in radians -->
<camera fovy="0.9599" .../>  
<!-- 45° in radians -->
<camera fovy="0.7854" .../> 
```

## Coordinate System Details

**MuJoCo Convention**:
- `cam_xmat[:, 0]`: Right (+X)
- `cam_xmat[:, 1]`: Up (+Y)
- `cam_xmat[:, 2]`: Forward (+Z)

**OpenGL/3DGS Convention**:
- Right: +X
- Up: +Y
- Forward: -Z (into screen)

**Conversion**:
```python
# MuJoCo rotation matrix (camera→world)
R_mujoco = data.cam_xmat[camera_id].reshape(3, 3)

# Convert to OpenGL
R_opengl = R_mujoco.copy()
R_opengl[:, 2] = -R_opengl[:, 2]  # Flip forward direction

# Build view matrix (world→camera)
R_view = R_opengl.T
t_view = -R_view @ camera_position
```

## Testing
Run demos to verify alignment:
```bash
TORCH_CUDA_ARCH_LIST="8.6" python examples/yam_standalone_demo.py
TORCH_CUDA_ARCH_LIST="8.6" python examples/quality_comparison_demo.py
```

Expected: 3DGS background matches MuJoCo camera viewpoint exactly.

## CUDA Compilation Fix
RTX 4090 (compute_89) with CUDA 11.6 nvcc causes compilation errors. Workaround:
```bash
TORCH_CUDA_ARCH_LIST="8.6" python script.py
```
This forces compilation for compute_86 which still works on RTX 4090.
