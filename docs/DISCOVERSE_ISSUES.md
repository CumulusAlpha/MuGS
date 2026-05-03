# DISCOVERSE Integration Issues & Solutions

## Summary

DISCOVERSE integration is **90% complete** with some format compatibility issues remaining.

## What Works ✅

1. **Robot + Task Loading**: Using `make_env()` to combine robot and task XML
2. **Camera FOV Fix**: Proper handling of degree/radian conversion
3. **Robot Geom Extraction**: Identifying robot geoms by body membership (24 geoms for AIRBOT Play)
4. **Custom Camera Creation**: Programmatically adding cameras with correct orientation
5. **MuGS Rendering**: Hybrid 3DGS + MuJoCo rendering pipeline

## Current Issues ❌

### 1. DISCOVERSE 3DGS Compressed Format

**Problem**: DISCOVERSE uses a **compressed/packed 3DGS format** that differs from standard 3DGS:

**Standard 3DGS PLY format**:
```
element vertex N
property float x
property float y  
property float z
property float scale_0
property float scale_1
property float scale_2
property float rot_0
...
```

**DISCOVERSE compressed format**:
```
element chunk M
property float min_x
property float max_x
...

element vertex N
property uint packed_position   # 4-byte packed XYZ
property uint packed_rotation   # 4-byte packed quaternion
property uint packed_scale      # 4-byte packed scales
property uint packed_color      # 4-byte packed RGB
```

**Impact**: Cannot directly load DISCOVERSE 3DGS files with current MuGS implementation.

**Example**: 
- File: `data/external/DISCOVERSE/models/3dgs/scene/lab3/point_cloud.ply`
- Format: Compressed (351,605 vertices, 1,374 chunks)
- Error: `ValueError: no field of name x`

### 2. Default Camera Orientation

**Problem**: DISCOVERSE's default `eye_side` camera looks **away** from the task workspace.

**Details**:
- Camera position: `[-0.324, 0.697, 1.02]`
- Camera forward: `[-0.396, -0.585, 0.708]`
- Task objects (cup, plate, robot) at: `[~0, ~1.0, ~0.7]`
- Dot product: -0.98 (objects are **behind** camera!)

**Why**: DISCOVERSE uses the `free_camera` (interactive viewer camera) for visualization, not the fixed MJCF cameras which are for robot observations.

**Solution**: Create custom camera programmatically (see `discoverse_with_custom_camera.py`).

## Workarounds

### Workaround 1: Use Standard Format 3DGS

Use any standard-format 3DGS scene (even if not matching the MJCF scene):

```python
config = GaussianSensorConfig(
    background_ply_path=Path("data/pretrained/kitchen/point_cloud/iteration_30000/point_cloud.ply"),
    # ... other params
)
```

**Pros**: Works immediately, demonstrates hybrid rendering
**Cons**: Background doesn't match MuJoCo scene geometry

### Workaround 2: Custom Camera

Add properly oriented camera to MJCF:

```python
def add_custom_camera_to_xml(xml_path):
    # Position camera to look at workspace
    cam_pos = [-0.5, 0.3, 1.3]
    lookat = [0.0, 1.0, 0.75]
    
    # Compute xyaxes...
    # Add <camera> element to worldbody
```

See `examples/discoverse_with_custom_camera.py` for full implementation.

## Roadmap to Full DISCOVERSE Support

### Short-term (Current)

- [x] Load DISCOVERSE tasks with `make_env()`
- [x] Fix camera FOV bug
- [x] Extract robot geoms by body
- [x] Create custom cameras
- [x] Document format issues

### Mid-term (TODO)

- [ ] Implement DISCOVERSE compressed format unpacker
- [ ] Add `load_compressed_ply()` function to GaussianSensor
- [ ] Test with all 12+ DISCOVERSE tasks
- [ ] Download and test object-level 3DGS files

### Long-term (Nice to have)

- [ ] Real-time hierarchical 3DGS streaming (DISCOVERSE's approach)
- [ ] Dynamic object composition (robot + objects each with 3DGS)
- [ ] Level-of-detail (LOD) based on camera distance

## How to Decompress DISCOVERSE Format

The packed fields use 4-byte (uint32) encoding. Likely schemes:

**Packed Position (uint32 → float3)**:
- Could be quantized floats with bounding box from `chunk` element
- Formula: `position = min_xyz + (packed / 2^32) * (max_xyz - min_xyz)`

**Packed Rotation (uint32 → quat)**:
- Quaternions have 4 components but only 3 DOF
- Could use smallest-3 encoding
- Or octahedral encoding

**Packed Scale (uint32 → float3)**:
- Similar to position, quantized within min/max range

**Packed Color (uint32 → RGB + opacity)**:
- Likely 8 bits each: `(R, G, B, A) = ((packed >> 24) & 0xFF, ...)`

To verify, would need to:
1. Check DISCOVERSE's `gaussian_renderer` module source
2. Or reverse-engineer by comparing compressed vs uncompressed versions

## References

- **DISCOVERSE Code**: `data/external/DISCOVERSE/discoverse/`
- **3DGS Download**: `discoverse/utils/download_from_huggingface.py`
- **HuggingFace Repo**: https://huggingface.co/tatp/DISCOVERSE-models
- **Working Demo**: `examples/discoverse_with_custom_camera.py`
- **Camera Debug**: `examples/debug_camera_alignment.py`

## Example Usage (Current State)

```bash
# 1. Clone DISCOVERSE
git clone https://github.com/TATP-233/DISCOVERSE data/external/DISCOVERSE

# 2. Run demo with standard 3DGS (works now)
TORCH_CUDA_ARCH_LIST="8.6" python examples/discoverse_with_custom_camera.py

# 3. Output: Hybrid rendering with mismatched background
# → MuJoCo shows DISCOVERSE task
# → 3DGS shows pretrained kitchen
# → Demonstrates hybrid rendering capability

# Future: When compressed format is supported
# → Both will show matching DISCOVERSE lab3 scene
```

## Contact

For questions about DISCOVERSE format:
- DISCOVERSE GitHub: https://github.com/TATP-233/DISCOVERSE
- Issue tracker: File issue in DISCOVERSE repo

For MuGS support questions:
- Check `/home/ununtu/metabot-workspace/mugs/docs/`
- Or file issue in MuGS repo
