# MuGS Showcase Materials

This directory contains scripts and examples for generating demonstration materials.

## Generated Materials

### AndroidTwin × G1 hybrid (`showcase/androidtwin_g1/`)
Unitree G1 humanoid in the INRIA kitchen scene — pipeline panel,
static-vs-tracked bg comparison, and 16-frame animation. Full
write-up in the project [`README`](../README.md#androidtwin--mugs--g1-humanoid-in-inria-kitchen).

### Static Showcase Image
**File**: `mugs_showcase.jpg`

Three-panel comparison showing:
- **Left**: MuJoCo simulation (physics-accurate but unrealistic visuals)
- **Middle**: 3D Gaussian Splatting (photorealistic but no physics)
- **Right**: MuGS Hybrid (best of both worlds)

Use for: Papers, presentations, README

### Animated Demo
**File**: `mugs_demo.gif`

8-frame animation showing robot pick-and-place motion with MuGS rendering.
- Loop: forward + reverse playback
- Frame rate: 500ms per frame
- Demonstrates real-time hybrid rendering

## Generating Showcase Materials

### Quick Generation
```bash
cd /home/ununtu/metabot-workspace/mugs
TORCH_CUDA_ARCH_LIST="8.6" python examples/yam_standalone_demo.py
```

This creates individual component images in `outputs/yam_standalone_demo/`.

### Custom Showcase Image
```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig

# Render with return_components=True
result = sensor.render(model, data, camera_name, return_components=True)

# Access components
mujoco_only = result['foreground']   # Physics simulation
background = result['background']    # 3DGS photorealistic
hybrid = result['rgb']              # MuGS hybrid
mask = result['mask']               # Blending mask
```

### Custom Animation
See `examples/yam_wrist_camera_demo.py` for keyframe animation example.

Key steps:
1. Define motion keyframes (joint positions)
2. Render each frame with MuGS
3. Collect frames and save as GIF with PIL

## Camera Viewpoints

### Task Observation Camera (Wrist-Mounted)
- **Camera**: `robot/camera_d405` on YAM link_6
- **View**: First-person gripper perspective
- **Use**: Matches actual RL task observations
- **Demo**: `examples/yam_wrist_camera_demo.py`

### Showcase Camera (Side View)
- **Camera**: Fixed third-person view
- **View**: Shows full scene and robot motion
- **Use**: Better visual impact for demonstrations
- **Demo**: `examples/yam_standalone_demo.py`

## Tips

### High-Quality Rendering
- Use 640×480 or higher resolution
- Add good lighting in scene XML
- Set `headlight ambient="0.5 0.5 0.5"` for visibility

### CUDA Compilation
RTX 4090 with CUDA 11.6 requires:
```bash
TORCH_CUDA_ARCH_LIST="8.6" python script.py
```

### Performance
- Hybrid rendering: ~5000 FPS (640×480)
- Background caching enabled by default
- First render loads PLY (~2 seconds), subsequent renders are fast

## Examples

### Paper Figure
Use `mugs_showcase.jpg` - clean three-panel comparison with annotations.

### Video/GIF
Use `mugs_demo.gif` or generate custom animation showing:
- Robot manipulation tasks
- Multiple camera angles
- Different objects/scenes

### Interactive Demo
Use `yam_standalone_demo.py` as starting point for real-time demos.
