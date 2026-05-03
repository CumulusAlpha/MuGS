# DISCOVERSE Integration Guide

Quick reference for using DISCOVERSE assets and tasks with MuGS.

## Overview

DISCOVERSE provides:
- ✅ **3DGS Assets**: Scene-level and object-level Gaussian Splatting (`.ply`)
- ✅ **Task Definitions**: MJCF files (`.xml`) for manipulation tasks
- ✅ **Robot Models**: URDF and MJCF for AIRBOT Play and MMK2
- ✅ **Auto-Download**: Assets automatically fetched from Hugging Face

## Installation

```bash
# Clone DISCOVERSE repository
cd data/external
git clone https://github.com/TATP-233/DISCOVERSE
cd DISCOVERSE

# Install Git LFS (if not already installed)
git lfs install
git lfs pull

# Install dependencies
pip install -r requirements.txt
```

## Directory Structure

```
DISCOVERSE/
├── models/
│   ├── 3dgs/              # Gaussian Splatting models
│   │   ├── scene/         # Background scenes
│   │   ├── object/        # Manipulable objects
│   │   ├── manipulator/   # Robot arms
│   │   └── ...
│   ├── mjcf/              # MuJoCo XML task definitions
│   │   ├── task_environments/
│   │   └── tasks_mmk2/
│   ├── urdf/              # Robot descriptions
│   ├── meshes/            # Geometry meshes
│   └── textures/          # Material textures
└── examples/
    └── tasks_*/           # Task example scripts
```

## Available Tasks

### Manipulation Tasks

| Task | Description | MJCF File | Robot |
|------|-------------|-----------|-------|
| `stack_block` | Stack blocks | `mjcf/task_environments/stack_block.xml` | Generic |
| `pan_pick` | Pick up pan | `mjcf/tasks_mmk2/pan_pick.xml` | MMK2 |
| `place_coffeecup` | Place coffee cup | Auto-generated | AIRBOT Play |
| `kiwi_pick` | Pick kiwi fruit | Auto-generated | MMK2 |
| `block_bridge_place` | Bridge placement | - | Generic |
| `close_laptop` | Close laptop | - | Generic |
| `cover_cup` | Cover cup | - | Generic |
| `open_drawer` | Open drawer | - | Generic |
| `peg_in_hole` | Peg insertion | - | Generic |
| `pick_jujube` | Pick jujube | - | AIRBOT Play |

### Robots

- **AIRBOT Play**: Lightweight 6-DOF manipulator
- **AIRBOT MMK2**: Dual-arm humanoid mobile manipulator

## Using DISCOVERSE with MuGS

### Example 1: Load DISCOVERSE Scene

```python
import mujoco
from pathlib import Path
from mugs.sensors import GaussianSensor, GaussianSensorConfig

# Path to DISCOVERSE
discoverse_dir = Path("data/external/DISCOVERSE")

# Load task environment
task_xml = discoverse_dir / "models/mjcf/task_environments/stack_block.xml"
model = mujoco.MjModel.from_xml_path(str(task_xml))
data = mujoco.MjData(model)

# Find corresponding 3DGS scene
scene_ply = discoverse_dir / "models/3dgs/scene/kitchen_01.ply"

# Configure MuGS sensor
config = GaussianSensorConfig(
    width=640,
    height=480,
    background_ply_path=scene_ply,
    render_mode="hybrid",
    robot_geom_names=["robot_link0", "robot_link1", "..."],  # Extract from MJCF
)

sensor = GaussianSensor(config)

# Render
result = sensor.render(model, data, "camera_name")
```

### Example 2: Extract Robot Geoms from MJCF

```python
import mujoco
import xml.etree.ElementTree as ET

def extract_robot_geoms(mjcf_path):
    """Extract all geom names from MJCF file."""
    tree = ET.parse(mjcf_path)
    root = tree.getroot()
    
    geoms = []
    for geom in root.iter('geom'):
        name = geom.get('name')
        if name:
            geoms.append(name)
    
    return geoms

# Usage
mjcf_path = "data/external/DISCOVERSE/models/mjcf/task_environments/stack_block.xml"
robot_geoms = extract_robot_geoms(mjcf_path)
print(f"Found {len(robot_geoms)} geoms: {robot_geoms}")
```

### Example 3: Run DISCOVERSE Task with MuGS

```python
#!/usr/bin/env python3
"""
Run DISCOVERSE manipulation task with MuGS rendering
"""

import mujoco
import numpy as np
from pathlib import Path
from mugs.sensors import GaussianSensor, GaussianSensorConfig

def run_discoverse_task(task_name="stack_block"):
    discoverse_dir = Path("data/external/DISCOVERSE")
    
    # Load task MJCF
    task_xml = discoverse_dir / f"models/mjcf/task_environments/{task_name}.xml"
    
    if not task_xml.exists():
        print(f"❌ Task not found: {task_xml}")
        return
    
    print(f"Loading task: {task_name}")
    model = mujoco.MjModel.from_xml_path(str(task_xml))
    data = mujoco.MjData(model)
    
    # Find available cameras
    camera_names = [model.camera(i).name for i in range(model.ncam)]
    print(f"Available cameras: {camera_names}")
    
    camera_name = camera_names[0] if camera_names else None
    
    # Find 3DGS scene (auto-downloaded on first use)
    scene_dir = discoverse_dir / "models/3dgs/scene"
    ply_files = list(scene_dir.glob("*.ply")) if scene_dir.exists() else []
    
    if ply_files:
        scene_ply = ply_files[0]
        print(f"Using 3DGS scene: {scene_ply}")
    else:
        print("⚠️  No 3DGS scenes found. They will be auto-downloaded on first run.")
        return
    
    # Extract geom names for foreground
    geom_names = [model.geom(i).name for i in range(model.ngeom)]
    robot_geoms = [name for name in geom_names if name and not name.startswith("floor")]
    
    print(f"Robot geoms: {len(robot_geoms)}")
    
    # Configure MuGS
    config = GaussianSensorConfig(
        width=640,
        height=480,
        background_ply_path=scene_ply,
        render_mode="hybrid",
        robot_geom_names=robot_geoms,
    )
    
    sensor = GaussianSensor(config)
    
    # Run simulation
    mujoco.mj_forward(model, data)
    
    if camera_name:
        result = sensor.render(model, data, camera_name, return_components=True)
        
        # Save result
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(result['foreground'])
        axes[0].set_title('MuJoCo')
        axes[1].imshow(result['background'])
        axes[1].set_title('3DGS (DISCOVERSE)')
        axes[2].imshow(result['rgb'])
        axes[2].set_title('MuGS Hybrid')
        
        for ax in axes:
            ax.axis('off')
        
        output_path = f"outputs/discoverse/{task_name}.jpg"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()
    else:
        print("❌ No camera found in scene")

if __name__ == "__main__":
    run_discoverse_task("stack_block")
```

## Asset Auto-Download

DISCOVERSE automatically downloads 3DGS PLY files from Hugging Face when needed:

1. First run detects missing assets
2. Downloads from HF repository
3. Caches locally in `models/3dgs/`
4. Subsequent runs use cached files

**No manual download required!**

## Comparing DISCOVERSE vs MuGS

| Feature | DISCOVERSE | MuGS |
|---------|------------|------|
| **3DGS Format** | PLY (auto-download) | PLY (manual) |
| **Tasks** | 12+ predefined | Custom |
| **Robots** | AIRBOT Play, MMK2 | Any MuJoCo robot |
| **Integration** | ROS support | mjlab/IsaacLab |
| **Focus** | Real2Sim2Real | Hybrid rendering |

**Use Together**:
- Use DISCOVERSE tasks/scenes
- Render with MuGS for performance
- Compare Sim2Real transfer

## Troubleshooting

### Missing 3DGS Files

**Problem**: `FileNotFoundError: *.ply not found`

**Solution**: Run DISCOVERSE examples first to trigger auto-download:
```bash
cd data/external/DISCOVERSE
python examples/tasks_airbot_play/place_coffeecup.py
```

### Camera Not Found

**Problem**: No camera defined in MJCF

**Solution**: Add camera to MJCF:
```xml
<mujoco>
  <worldbody>
    <camera name="main_cam" pos="1 -1 1" xyaxes="1 0 0 0 1 1"/>
  </worldbody>
</mujoco>
```

### Geom Names Empty

**Problem**: `robot_geom_names` is empty

**Solution**: Check MJCF has named geoms:
```python
model = mujoco.MjModel.from_xml_path(mjcf_path)
for i in range(model.ngeom):
    print(f"Geom {i}: {model.geom(i).name}")
```

## Resources

- **DISCOVERSE GitHub**: https://github.com/TATP-233/DISCOVERSE
- **DISCOVERSE Website**: https://air-discoverse.github.io/
- **Paper**: https://arxiv.org/abs/2507.21981
- **MuGS Docs**: `docs/`

## Citation

```bibtex
@article{discoverse2025,
  title={DISCOVERSE: Efficient Robot Simulation in Complex High-Fidelity Environments},
  author={Jia, Yufei and others},
  journal={IROS},
  year={2025}
}
```
