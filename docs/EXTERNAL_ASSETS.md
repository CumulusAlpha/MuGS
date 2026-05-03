# External Assets Tutorial

This guide explains how to download and use 3DGS assets from related projects like GS-Playground and DISCOVERSE.

## Quick Start

### List Available Sources
```bash
python scripts/download_external_assets.py list
```

### Download Specific Assets
```bash
# Download GS-Playground repository
python scripts/download_external_assets.py gs-playground

# Download Bridge-GS dataset (Hugging Face)
python scripts/download_external_assets.py bridge-gs

# Download InteriorGS scenes
python scripts/download_external_assets.py interior-gs
```

## Available Asset Sources

### 1. GS-Playground (RSS 2026)

**What**: High-throughput photorealistic simulator with manipulation benchmarks

**Content**:
- Example 3DGS scenes
- Robot assets (Franka, Robotiq)
- Benchmark task definitions
- Bridge-GS dataset (via Hugging Face)

**Download**:
```bash
python scripts/download_external_assets.py gs-playground -o data/external
```

**GitHub**: https://github.com/discoverse-dev/gs_playground

**Paper**: https://arxiv.org/abs/2604.25459

**Assets**:
- Compressed 3DGS assets
- Scene-level reconstructions
- Object-level 3DGS + meshes
- Camera calibrations

---

### 2. DISCOVERSE

**What**: Unified 3DGS-based simulation framework for Real2Sim2Real

**Content**:
- Real-world scene reconstructions
- ROS-compatible robot models
- Auto-downloading PLY assets from Hugging Face

**Download**:
```bash
# Clone the repository
git clone https://github.com/TATP-233/DISCOVERSE
cd DISCOVERSE
git lfs install
git lfs pull

# Or use our script
python scripts/download_external_assets.py discoverse
```

**Note**: DISCOVERSE automatically downloads PLY models when you run simulations.

**GitHub**: https://github.com/TATP-233/DISCOVERSE

**Website**: https://air-discoverse.github.io/

**Paper**: https://arxiv.org/abs/2507.21981

---

### 3. Bridge-GS Dataset

**What**: Large-scale manipulation dataset with 3DGS reconstructions

**Content**:
- Scene-level 3DGS (full environments)
- Object-level 3DGS (individual objects)
- Object meshes
- 6D object poses
- Camera intrinsics & extrinsics

**Based on**: Bridge-v2 dataset

**Download**:
```bash
python scripts/download_external_assets.py bridge-gs

# Or use Hugging Face CLI directly
huggingface-cli download YLab-Open/BRIDGE-Open --repo-type dataset
```

**Hugging Face**: https://huggingface.co/datasets/YLab-Open/BRIDGE-Open

**Use Cases**:
- Manipulation task training
- Visual policy learning
- Sim2Real transfer benchmarks

---

### 4. InteriorGS

**What**: Semantically labeled indoor scenes with 3DGS

**Download**:
```bash
python scripts/download_external_assets.py interior-gs
```

**Hugging Face**: https://huggingface.co/datasets/spatialverse/InteriorGS

## Using External Assets with MuGS

### Example 1: Load Bridge-GS Scene

```python
from pathlib import Path
from mugs.sensors import GaussianSensor, GaussianSensorConfig

# Path to downloaded Bridge-GS asset
bridge_gs_dir = Path("data/external/bridge-gs")
scene_ply = bridge_gs_dir / "scenes" / "kitchen_scene_01" / "point_cloud.ply"

# Configure sensor with Bridge-GS background
config = GaussianSensorConfig(
    width=640,
    height=480,
    background_ply_path=scene_ply,
    render_mode="hybrid",
    robot_geom_names=["panda_link0", "panda_link1", "..."],
)

sensor = GaussianSensor(config)

# Render
result = sensor.render(model, data, camera_name)
```

### Example 2: Use DISCOVERSE Scene

```python
# DISCOVERSE scenes are in MJCF format with embedded 3DGS references
import mujoco

# Load DISCOVERSE scene
discoverse_scene = "data/external/DISCOVERSE/models/kitchen/scene.xml"
model = mujoco.MjModel.from_xml_path(discoverse_scene)
data = mujoco.MjData(model)

# Extract 3DGS path from scene (if specified)
# Or manually specify the background
ply_path = "data/external/DISCOVERSE/models/kitchen/gaussian.ply"

config = GaussianSensorConfig(
    background_ply_path=ply_path,
    render_mode="hybrid",
    # ... robot geoms from MJCF
)
```

### Example 3: Create Custom Scene with External Background

```python
import mujoco
from mugs.sensors import GaussianSensor, GaussianSensorConfig

# Your robot MJCF
robot_xml = """
<mujoco>
  <worldbody>
    <!-- Your robot definition -->
  </worldbody>
</mujoco>
"""

model = mujoco.MjModel.from_xml_string(robot_xml)
data = mujoco.MjData(model)

# Use downloaded 3DGS background
config = GaussianSensorConfig(
    background_ply_path="data/external/interior-gs/living_room/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["base", "link1", "link2"],
)

sensor = GaussianSensor(config)
result = sensor.render(model, data, "camera")
```

## Installation Requirements

### For Hugging Face Downloads

```bash
pip install huggingface-hub
```

### For Git LFS (Large Files)

```bash
# Ubuntu/Debian
sudo apt-get install git-lfs
git lfs install

# macOS
brew install git-lfs
git lfs install
```

## Asset Directory Structure

After downloading, assets are organized as:

```
data/external/
├── gs_playground/           # GS-Playground repository
│   ├── assets/
│   │   ├── scenes/
│   │   └── robots/
│   └── README.md
│
├── bridge-gs/               # Bridge-GS dataset
│   ├── scenes/
│   │   ├── kitchen_01/
│   │   │   ├── point_cloud.ply
│   │   │   ├── objects/
│   │   │   └── calibration.json
│   │   └── ...
│   └── metadata.json
│
├── interior-gs/             # InteriorGS scenes
│   ├── living_room/
│   │   ├── point_cloud.ply
│   │   └── semantic_labels.json
│   └── ...
│
└── DISCOVERSE/              # DISCOVERSE framework
    ├── models/
    │   └── kitchen/
    │       ├── scene.xml
    │       └── gaussian.ply
    └── ...
```

## Benchmarking with External Assets

### Compare MuGS vs GS-Playground Performance

```python
import time
import numpy as np

# Your MuGS setup
mugs_sensor = GaussianSensor(config)

# Benchmark
n_frames = 1000
start = time.time()
for _ in range(n_frames):
    result = mugs_sensor.render(model, data, camera_name)
elapsed = time.time() - start

fps = n_frames / elapsed
print(f"MuGS: {fps:.1f} FPS")
```

### Use Bridge-GS Tasks

Bridge-GS provides manipulation task definitions. To use them:

1. Download Bridge-GS dataset
2. Load task definition (JSON/YAML)
3. Set up MuJoCo scene with specified objects
4. Use corresponding 3DGS background

```python
import json

# Load task definition
task_file = "data/external/bridge-gs/tasks/pick_place_01.json"
with open(task_file) as f:
    task = json.load(f)

# task contains:
# - scene_id: which 3DGS background to use
# - objects: object models and poses
# - camera: camera parameters
# - goal: task goal specification
```

## Troubleshooting

### Download Fails

**Problem**: Hugging Face download times out

**Solution**:
```bash
# Use git-lfs instead
python scripts/download_external_assets.py bridge-gs --use-git-lfs
```

### Large File Sizes

**Problem**: PLY files are very large (GB+)

**Solutions**:
- Download only specific scenes you need
- Use compressed formats if available
- Check disk space: `df -h`

### Camera Alignment Issues

**Problem**: External 3DGS background doesn't align with MuJoCo camera

**Solution**:
- Check camera calibration files in the dataset
- Verify FOV units (degrees vs radians)
- Ensure coordinate system matches (see `docs/CAMERA_ALIGNMENT_FIX.md`)

## Related Work Comparison

| Project | FPS | Physics | Assets | Tasks | License |
|---------|-----|---------|--------|-------|---------|
| **MuGS** | ~5K | MuJoCo | Kitchen (1) | Custom | MIT |
| **GS-Playground** | ~10K | Parallel MuJoCo | Bridge-GS (100+) | Locomotion + Manipulation | Check repo |
| **DISCOVERSE** | ? | MuJoCo | Auto-download | General | MIT |

## Citation

If you use these external assets, please cite the original works:

```bibtex
@article{gsplayground2026,
  title={GS-Playground: A High-Throughput Photorealistic Simulator for Vision-Informed Robot Learning},
  journal={RSS},
  year={2026}
}

@article{discoverse2025,
  title={DISCOVERSE: Efficient Robot Simulation in Complex High-Fidelity Environments},
  year={2025}
}
```

## Resources

- **GS-Playground Paper**: https://arxiv.org/abs/2604.25459
- **DISCOVERSE Paper**: https://arxiv.org/abs/2507.21981
- **Awesome 3DGS Robotics**: https://github.com/zstsandy/Awesome-3D-Gaussian-Splatting-in-Robotics
- **MuGS Documentation**: `docs/`
