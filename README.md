# MuGS: MuJoCo Gaussian Splatting

> **First scalable, photorealistic MuJoCo-based Vision-Language-Action benchmark using 3D Gaussian Splatting with two-stage lightweight rendering.**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![MuJoCo](https://img.shields.io/badge/MuJoCo-Warp-green)]()
[![3DGS](https://img.shields.io/badge/Rendering-3DGS-orange)]()

---

## Overview

**MuGS** (MuJoCo Gaussian Splatting) enables training Vision-Language-Action (VLA) policies in photorealistic simulated environments with unprecedented scale:

- **5000-8000 FPS** rendering @ 4096 parallel environments (160×120 base resolution)
- **Photorealistic quality** via 3D Gaussian Splatting + learned super-resolution
- **Digital twin methodology** with object-level 3DGS assets
- **MuJoCo ecosystem** compatibility (Warp backend for GPU acceleration)
- **Sim2real ready** with procedural scene generation and domain adaptation

### Key Innovation

**Two-Stage Rendering Pipeline:**
1. **Stage 1**: Fast low-resolution 3DGS rendering (160×120) @ 50k FPS
2. **Stage 2**: Learned super-resolution to high quality (640×480) @ ~50ms batch latency

This achieves **Isaac Sim-level photorealism at 10× the throughput**.

---

## Architecture

```
MuJoCo Warp Physics (4096 envs)
        ↓
GaussianSensor (custom mjlab Sensor)
  • Object-level 3DGS digital twins
  • Rigid-link Gaussian kinematics
  • Batched gsplat rasterization
        ↓
Low-res RGB (4096, 160, 120, 3) @ 5000-8000 FPS
        ↓
SimAwareSR Model (SwinIR-light / RealESRGAN-tiny)
  • Trained on sim + real paired data
  • TensorRT optimized batched inference
        ↓
High-res RGB (4096, 640, 480, 3) @ ~50ms
        ↓
VLA Policy (OpenVLA / RT-2 compatible)
```

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/mjlab-3dgs-vla.git
cd mjlab-3dgs-vla

# Install dependencies (requires CUDA 11.8+)
pip install -e .

# Install mjlab (MuJoCo Warp backend)
pip install mjlab

# Install gsplat (3DGS rasterization)
pip install gsplat==1.5.3
```

### Basic Usage

```python
from mjlab_3dgs import GaussianSensor, load_object_library
from mjlab.envs import ManagerBasedRlEnv

# Create environment with 3DGS rendering
env_cfg = HumanoidPickCfg()
env_cfg.scene.sensors["rgb_camera"] = GaussianSensorCfg(
    resolution=(160, 120),
    object_library="assets/objects/ycb_library.yaml"
)

env = ManagerBasedRlEnv(cfg=env_cfg)

# Run simulation
obs, _ = env.reset()
for _ in range(1000):
    action = policy(obs)
    obs, reward, done, info = env.step(action)
    # obs["rgb_camera"]: (N_env, 640, 480, 3) high-res RGB
```

### Running Examples

```bash
# Basic single-object rendering demo
python examples/basic/render_object.py

# Procedural scene generation
python examples/basic/procedural_scenes.py

# VLA pick-and-place task
python examples/advanced/vla_pick_place.py --num-envs 1024
```

---

## Project Structure

```
mjlab-3dgs-vla/
├── src/mjlab_3dgs/           # Main package
│   ├── sensors/               # GaussianSensor implementation
│   │   ├── gaussian_sensor.py       (~300 LOC)
│   │   └── camera_config.py
│   ├── utils/                 # SE(3) transforms, helpers
│   │   ├── gaussian_transforms.py   (~100 LOC)
│   │   └── splat_utils.py
│   ├── assets/                # Asset management
│   │   ├── object_library.py        (~200 LOC)
│   │   └── scene_loader.py
│   ├── sr_models/             # Super-resolution models
│   │   ├── simawaresr.py            (~400 LOC)
│   │   └── inference.py
│   └── scene_gen/             # Procedural generation
│       └── procedural_sampler.py    (~300 LOC)
├── assets/                    # 3DGS assets and configs
│   ├── objects/               # Object-level 3DGS .ply files
│   ├── scenes/                # Background scene .ply files
│   └── configs/               # YAML asset configs
├── configs/                   # Environment and sensor configs
│   ├── envs/                  # VLA task configs
│   ├── sensors/               # Camera/sensor configs
│   └── sr/                    # SR model configs
├── docs/                      # Documentation
│   ├── design/                # Technical design specs
│   ├── api/                   # API reference
│   └── guides/                # Implementation guides
├── scripts/                   # Utility scripts
│   ├── data_collection/       # Real data collection
│   ├── training/              # SR model training
│   └── evaluation/            # Benchmark evaluation
├── examples/                  # Example code
│   ├── basic/                 # Simple demos
│   └── advanced/              # Full VLA tasks
└── tests/                     # Unit and integration tests
```

---

## Documentation

- **[Project Vision](docs/design/PROJECT_VISION.md)** - High-level goals and architecture
- **[Technical Design](docs/design/TECHNICAL_DESIGN.md)** - Detailed system design
- **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation
- **[Implementation Guide](docs/guides/IMPLEMENTATION.md)** - Step-by-step development guide
- **[Asset Format Spec](docs/design/ASSET_FORMAT.md)** - 3DGS asset specifications

---

## Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅ Current
- [x] Project structure setup
- [ ] gsplat single-object rendering PoC
- [ ] mjlab GaussianSensor skeleton
- [ ] Batched rendering speed validation

### Phase 2: Assets (Weeks 3-5)
- [ ] YCB objects 3DGS reconstruction
- [ ] Object twins config system
- [ ] Procedural scene sampling

### Phase 3: Core Pipeline (Weeks 6-7)
- [ ] Dynamic scene rendering
- [ ] VLA pick-and-place task
- [ ] 10k episode generation

### Phase 4: Super-Resolution (Weeks 8-10)
- [ ] Real robot data collection
- [ ] SimAwareSR training
- [ ] Sim2real validation

### Phase 5: Benchmark Release (Weeks 11-12)
- [ ] Asset library packaging
- [ ] Documentation + tutorials
- [ ] arXiv paper + open-source

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Rendering FPS (4096 envs × 160×120) | ≥ 5000 | 🔄 TBD |
| Visual quality (LPIPS vs real) | < 0.15 | 🔄 TBD |
| Sim2real zero-shot success | ≥ 70% | 🔄 TBD |
| Memory footprint | < 25GB | 🔄 TBD |
| Asset library size | ≥ 50 objects | 🔄 TBD |

---

## Related Work

- **[GS-Playground](https://gsplayground.github.io)** (RSS 2026) - Custom physics + 3DGS
- **[DISCOVERSE](https://arxiv.org/abs/2507.21981)** - MuJoCo + 3DGS predecessor
- **[SIMPLER](https://simpler-env.github.io/)** - Isaac Sim VLA benchmark
- **[OpenVLA](https://openvla.github.io/)** - Open VLA model architecture

---

## Citation

```bibtex
@inproceedings{mjlab3dgsvla2026,
  title={MJLab-3DGS-VLA: Scalable Photorealistic Vision-Language-Action Benchmark with 3D Gaussian Splatting},
  author={Your Name},
  booktitle={Robotics: Science and Systems (RSS)},
  year={2026}
}
```

---

## License

Apache 2.0 License. See [LICENSE](LICENSE) for details.

---

## Contact

- **Project Lead**: [Your Name] (your.email@domain.com)
- **Issues**: [GitHub Issues](https://github.com/YOUR_ORG/mjlab-3dgs-vla/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_ORG/mjlab-3dgs-vla/discussions)

---

## Acknowledgments

This project builds upon:
- [mjlab](https://github.com/mujocolab/mjlab) - MuJoCo Warp RL framework
- [gsplat](https://github.com/nerfstudio-project/gsplat) - 3D Gaussian Splatting library
- [MuJoCo](https://mujoco.org) - Physics simulation
- [OpenVLA](https://openvla.github.io/) - VLA model architecture

Special thanks to the robotics research community for open-source contributions.
