# MuGS Project Overview

**MuGS**: MuJoCo Gaussian Splatting  
**Version**: 0.1.0  
**Status**: Phase 0 Complete, Ready for Implementation  
**Last Updated**: 2026-05-02

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Architecture](#project-architecture)
3. [Development Phases](#development-phases)
4. [Technical Stack](#technical-stack)
5. [File Organization](#file-organization)
6. [Asset Management](#asset-management)
7. [Performance Targets](#performance-targets)
8. [Getting Started](#getting-started)

---

## Executive Summary

### Mission
Build the first scalable, photorealistic MuJoCo-based Vision-Language-Action (VLA) benchmark using 3D Gaussian Splatting rendering.

### Key Innovation
**Two-Stage Rendering Pipeline:**
1. **Stage 1**: Fast low-resolution 3DGS rendering (160×120 @ 5000-8000 FPS)
2. **Stage 2**: Learned super-resolution upscaling (→ 640×480 photorealistic)

**Result**: 10× faster than Isaac Sim with comparable visual quality

### Target Impact
- First photorealistic MuJoCo VLA benchmark
- First robotics application of 3DGS + SR two-stage rendering
- Enable large-scale VLA policy training (10k+ episodes/hour)
- Publication target: RSS/CoRL 2026

---

## Project Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MuGS System Architecture                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  MuJoCo Physics  │  ← GPU-accelerated (Warp backend)
│  (4096 envs)     │
└────────┬─────────┘
         │ poses (SE(3))
         ▼
┌──────────────────────────────────────────────────────────────┐
│              Stage 1: 3DGS Rendering (gsplat)                 │
│  • Batched rendering: 4096 cameras simultaneously            │
│  • Low-res output: 160×120 RGB                               │
│  • Throughput: 5000-8000 FPS                                 │
│  • Latency: ~5ms per batch                                   │
└────────┬─────────────────────────────────────────────────────┘
         │ low-res images (Nx160x120x3)
         ▼
┌──────────────────────────────────────────────────────────────┐
│         Stage 2: Super-Resolution (SwinIR-light)             │
│  • Upscaling: 160×120 → 640×480                             │
│  • Model size: 900K params                                   │
│  • Latency: ~2ms per image                                   │
│  • Quality: LPIPS < 0.10                                     │
└────────┬─────────────────────────────────────────────────────┘
         │ high-res images (Nx640x480x3)
         ▼
┌──────────────────┐
│   VLA Policy     │  ← Vision-Language-Action model
│   Training       │
└──────────────────┘
```

### Component Breakdown

#### 1. Physics Engine (MuJoCo Warp)
- **Function**: Simulate robot dynamics and environment
- **Backend**: MuJoCo Warp (GPU-accelerated)
- **Parallelization**: 4096 environments on single GPU
- **Output**: Camera poses (position + orientation in SE(3))

#### 2. GaussianSensor (Custom)
- **Function**: Render photorealistic images from 3DGS assets
- **Backend**: gsplat library (batched 3DGS renderer)
- **Input**: Camera poses, 3DGS object models
- **Output**: Low-res RGB images (160×120×3)
- **Performance**: 5000-8000 FPS for 4096 parallel cameras

#### 3. SimAwareSR (Custom)
- **Function**: Super-resolution upscaling with sim-aware features
- **Backend**: SwinIR-light + custom sim features
- **Input**: Low-res images + optional (depth, segmentation)
- **Output**: High-res images (640×480×3)
- **Performance**: <2ms per image

#### 4. Object Library
- **Function**: Manage 3DGS digital twin assets
- **Format**: PLY (Gaussian parameters) + YAML (metadata)
- **Categories**: Kitchen, tools, containers, misc
- **Size**: 20+ objects in Phase 3

#### 5. Scene Generator
- **Function**: Procedurally generate diverse training scenes
- **Features**: Random placement, physics validation, diversity metrics
- **Templates**: Tabletop, kitchen, floor cleanup
- **Output**: Scene configs (HDF5)

---

## Development Phases

### Phase 0: Setup ✅ (Complete)
**Duration**: 2 days (2026-05-01 ~ 05-02)  
**Status**: ✅ Complete

**Deliverables**:
- [x] Project structure created
- [x] Documentation (12k+ words)
- [x] Python package scaffolding
- [x] Git initialized
- [x] Asset acquisition plan
- [x] Setup scripts

---

### Phase 1: gsplat Proof-of-Concept
**Duration**: 2 weeks  
**Goal**: Validate rendering performance targets  
**Status**: 🔄 Ready to start

#### Tasks
1. **Environment Setup** (Day 1-2)
   - [ ] Install gsplat (`pip install gsplat>=1.5.0`)
   - [ ] Download sample 3DGS models (see Asset Guide)
   - [ ] Verify GPU/CUDA setup
   - [ ] Test basic gsplat rendering

2. **Single-View Rendering** (Day 3-4)
   - [ ] Load 3DGS model from PLY file
   - [ ] Render single view at 640×480
   - [ ] Measure FPS and quality (LPIPS/PSNR)
   - [ ] Profile GPU memory usage

3. **Batched Rendering** (Day 5-7)
   - [ ] Implement batched camera pose generation
   - [ ] Render 4096 views in parallel
   - [ ] Measure throughput at different resolutions
   - [ ] Optimize batch size for best FPS

4. **MuJoCo Integration** (Day 8-10)
   - [ ] Create minimal MuJoCo scene
   - [ ] Extract camera pose from MuJoCo
   - [ ] Drive gsplat with MuJoCo camera
   - [ ] Synchronize physics + rendering loop

5. **Validation & Documentation** (Day 11-14)
   - [ ] Benchmark report (FPS, memory, quality)
   - [ ] Code review and cleanup
   - [ ] Update technical design doc
   - [ ] Demo notebook

**Success Criteria**:
- ✅ Batched rendering achieves >5000 FPS @ 160×120
- ✅ Single-view LPIPS < 0.15 vs ground truth
- ✅ MuJoCo camera integration working
- ✅ Demo script renders 10-sec video

---

### Phase 2: GaussianSensor Core
**Duration**: 3 weeks  
**Goal**: Production-ready sensor API  
**Status**: ⏸️ Waiting

#### Tasks
1. **Sensor API** (Week 1)
   - [ ] Implement `GaussianSensorCfg` dataclass
   - [ ] Implement `GaussianSensor` class
   - [ ] SE(3) transform utilities
   - [ ] Unit tests

2. **Object Library** (Week 2)
   - [ ] Implement `ObjectLibrary` class
   - [ ] Asset loading (PLY + YAML)
   - [ ] Memory-efficient caching
   - [ ] Download 5 sample objects

3. **Integration Tests** (Week 3)
   - [ ] Multi-object scenes
   - [ ] Dynamic object motion
   - [ ] Full pipeline benchmark
   - [ ] Documentation

**Success Criteria**:
- ✅ Sensor API complete with docs
- ✅ End-to-end latency <10ms for 4096 envs
- ✅ 5+ object assets working

---

### Phase 3: Object Library & Scenes
**Duration**: 3 weeks  
**Goal**: 20+ production assets + scene generation  
**Status**: ⏸️ Waiting

#### Tasks
1. **Asset Acquisition** (Week 1-2)
   - [ ] Download/capture 20+ object 3DGS models
   - [ ] Organize by category
   - [ ] Optimize file sizes
   - [ ] Quality validation

2. **Procedural Scenes** (Week 2-3)
   - [ ] Implement `SceneGenerator`
   - [ ] Scene templates (3 types)
   - [ ] Diversity metrics
   - [ ] Export pipeline (HDF5)

3. **Documentation** (Week 3)
   - [ ] Asset catalog with previews
   - [ ] Scene generation guide
   - [ ] Contribution guidelines

**Success Criteria**:
- ✅ 20+ production-quality assets
- ✅ Scene generator working
- ✅ Asset library documented

---

### Phase 4: Super-Resolution
**Duration**: 2 weeks  
**Goal**: Train SR model for sim2real quality  
**Status**: ⏸️ Waiting

#### Tasks
1. **Data Collection** (Week 1)
   - [ ] Generate 10k LR-HR pairs
   - [ ] Train/val/test split
   - [ ] Data pipeline (HDF5)

2. **Model Training** (Week 1-2)
   - [ ] Implement `SimAwareSR` model
   - [ ] Training loop (DDP)
   - [ ] Hyperparameter sweep
   - [ ] Export best checkpoint

3. **Evaluation** (Week 2)
   - [ ] Quantitative metrics
   - [ ] Qualitative comparison
   - [ ] Ablation studies

**Success Criteria**:
- ✅ SR model LPIPS <0.10
- ✅ Inference <2ms per image
- ✅ Ablation results documented

---

### Phase 5: Benchmarking & Paper
**Duration**: 2 weeks  
**Goal**: Publication-ready results  
**Status**: ⏸️ Waiting

#### Tasks
1. **Benchmark Suite** (Week 1)
   - [ ] 6 VLA tasks implemented
   - [ ] Baseline evaluations
   - [ ] Performance benchmarks

2. **Paper Writing** (Week 2)
   - [ ] Draft complete
   - [ ] All figures generated
   - [ ] Internal review

3. **Code Release** (Week 2)
   - [ ] Clean up code
   - [ ] Demo scripts
   - [ ] Unit tests >80% coverage
   - [ ] Release preparation

**Success Criteria**:
- ✅ Paper draft complete
- ✅ Benchmark results ready
- ✅ Code release-ready

---

## Technical Stack

### Core Dependencies

| Component | Library | Version | License | Purpose |
|-----------|---------|---------|---------|---------|
| Physics | MuJoCo Warp | TBD | Apache-2.0 | GPU-accelerated physics |
| Rendering | gsplat | ≥1.5.0 | Apache-2.0 | Batched 3DGS rendering |
| Deep Learning | PyTorch | ≥2.0.0 | BSD-3 | Neural networks |
| SR Backbone | SwinIR | - | Apache-2.0 | Super-resolution model |
| Image Quality | LPIPS | ≥0.1.4 | BSD-2 | Perceptual loss |
| Visualization | Matplotlib | ≥3.7.0 | PSF | Plotting & visualization |

### Optional Dependencies

| Component | Library | Purpose |
|-----------|---------|---------|
| Asset Capture | COLMAP | Structure-from-Motion |
| SR Optimization | TensorRT | Inference acceleration |
| Experiment Tracking | Weights & Biases | Training monitoring |
| 3D Processing | Trimesh | Mesh operations |

### Development Tools

- **Testing**: pytest, pytest-cov
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: Sphinx (future)
- **CI/CD**: GitHub Actions (future)

---

## File Organization

### Directory Structure

```
mugs/
├── .context/                    # Project memory & context
│   └── MEMORY.md               # Cross-session context
│
├── assets/                      # 3DGS assets & scene configs
│   ├── objects/                # 3DGS object models
│   │   ├── kitchen/           # Kitchen items (mug, plate, etc.)
│   │   ├── tools/             # Tools (hammer, screwdriver, etc.)
│   │   ├── containers/        # Containers (box, bowl, etc.)
│   │   └── misc/              # Miscellaneous objects
│   ├── scenes/                # Pre-generated scene configs
│   │   ├── tabletop/          # Tabletop manipulation scenes
│   │   ├── kitchen/           # Kitchen counter scenes
│   │   └── floor/             # Floor cleanup scenes
│   └── configs/               # Asset metadata (YAML)
│
├── configs/                     # Runtime configurations
│   ├── envs/                  # Environment configs
│   ├── sensors/               # Sensor configs
│   └── sr/                    # SR model configs
│
├── docs/                        # Documentation
│   ├── design/                # Technical design docs
│   │   └── TECHNICAL_DESIGN.md
│   ├── guides/                # User guides
│   │   ├── ASSET_ACQUISITION.md
│   │   ├── INSTALLATION.md
│   │   └── QUICK_START.md
│   ├── api/                   # API documentation (future)
│   └── RESEARCH_IDEAS.md
│
├── examples/                    # Example scripts
│   ├── basic/                 # Basic usage examples
│   │   ├── render_single_view.py
│   │   ├── render_batched.py
│   │   └── mujoco_integration.py
│   └── advanced/              # Advanced examples
│       ├── procedural_scenes.py
│       ├── sr_inference.py
│       └── vla_training.py
│
├── scripts/                     # Utility scripts
│   ├── data_collection/       # Data generation scripts
│   │   ├── download_assets.py
│   │   ├── generate_sr_dataset.py
│   │   └── capture_3dgs.sh
│   ├── training/              # Training scripts
│   │   ├── train_sr.py
│   │   └── train_vla.py
│   └── evaluation/            # Evaluation scripts
│       ├── benchmark_rendering.py
│       ├── benchmark_vla.py
│       └── compute_metrics.py
│
├── src/mugs/                    # Main Python package
│   ├── __init__.py
│   │
│   ├── sensors/               # Rendering & sensors
│   │   ├── __init__.py
│   │   ├── gaussian_sensor.py    # GaussianSensor class
│   │   ├── sensor_config.py      # GaussianSensorCfg
│   │   └── camera.py             # Camera utilities
│   │
│   ├── assets/                # Asset management
│   │   ├── __init__.py
│   │   ├── object_library.py     # ObjectLibrary class
│   │   ├── loader.py             # PLY/YAML loading
│   │   └── metadata.py           # Asset metadata handling
│   │
│   ├── scene_gen/             # Procedural scene generation
│   │   ├── __init__.py
│   │   ├── generator.py          # SceneGenerator class
│   │   ├── templates.py          # Scene templates
│   │   └── placement.py          # Object placement logic
│   │
│   ├── sr_models/             # Super-resolution models
│   │   ├── __init__.py
│   │   ├── sim_aware_sr.py       # SimAwareSR model
│   │   ├── swinir.py             # SwinIR backbone
│   │   └── losses.py             # Perceptual losses
│   │
│   └── utils/                 # Utilities
│       ├── __init__.py
│       ├── transforms.py         # SE(3) transforms
│       ├── rendering.py          # Rendering utilities
│       ├── metrics.py            # Image quality metrics
│       └── visualization.py      # Visualization tools
│
├── tests/                       # Unit & integration tests
│   ├── unit/                  # Unit tests
│   │   ├── test_sensors.py
│   │   ├── test_transforms.py
│   │   └── test_object_library.py
│   └── integration/           # Integration tests
│       ├── test_pipeline.py
│       └── test_scene_gen.py
│
├── .gitignore
├── LICENSE                      # Apache-2.0
├── PROJECT_MANIFEST.md          # Project index
├── PROJECT_OVERVIEW.md          # This file
├── pyproject.toml               # Python package config
├── README.md                    # Quick overview
└── TODO.md                      # Development task list
```

### Key Files

#### Documentation
- **README.md**: Quick project overview, installation, basic usage
- **PROJECT_OVERVIEW.md**: This file - comprehensive project reference
- **TODO.md**: Phase-by-phase task list with progress tracking
- **PROJECT_MANIFEST.md**: Document index and navigation
- **docs/design/TECHNICAL_DESIGN.md**: 8000+ word implementation guide
- **docs/RESEARCH_IDEAS.md**: Research questions and experiments

#### Configuration
- **pyproject.toml**: Python package metadata and dependencies
- **configs/**: Runtime configurations for envs, sensors, SR models

#### Code
- **src/mugs/**: Main package with 5 submodules
- **examples/**: Runnable example scripts
- **scripts/**: Utility scripts for data, training, evaluation

#### Development
- **tests/**: Unit and integration tests
- **.context/MEMORY.md**: Cross-session project context

---

## Asset Management

### Asset Types

#### 1. 3DGS Object Models
**Format**: `.ply` (Gaussian parameters)
- Position (x, y, z)
- Rotation (quaternion)
- Scale (3D)
- Color (RGB)
- Opacity (α)
- Spherical harmonics (SH coefficients)

**Metadata**: `.yaml` companion file
```yaml
name: "coffee_mug"
category: "kitchen"
size: [0.08, 0.08, 0.10]  # meters (x, y, z)
mass: 0.3  # kg
captured: "2024-03-15"
source: "custom_capture"
```

**Storage**:
- Path: `assets/objects/{category}/{name}.ply`
- Metadata: `assets/configs/{category}/{name}.yaml`

#### 2. Scene Configurations
**Format**: `.hdf5` (scene state snapshots)
- Object poses (SE(3))
- Object IDs
- Camera poses
- Lighting conditions

**Path**: `assets/scenes/{template}/{scene_id}.h5`

#### 3. Pre-trained Models
**SR Model**: `models/sr/sim_aware_sr.pt`
- SwinIR-light checkpoint (~3.5 MB)
- Training config
- Metadata (LPIPS, PSNR, training time)

**Path**: `models/{model_type}/{model_name}.pt`

### Asset Sources

See `docs/guides/ASSET_ACQUISITION.md` for detailed instructions.

#### Open-Source 3DGS Datasets
1. **Replica Dataset** - Indoor scenes (high quality)
2. **Objaverse-3DGS** - Large-scale object dataset
3. **NeRF Synthetic** - Simple shapes for testing
4. **Custom Captures** - COLMAP → 3DGS pipeline

#### Pre-trained Models
1. **SwinIR** - Super-resolution backbone (ImageNet pretrained)
2. **Real-ESRGAN** - Alternative SR model
3. **LPIPS** - Perceptual loss (VGG pretrained)

---

## Performance Targets

### Rendering Performance

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Rendering FPS (low-res) | 5000-8000 | TBD | @ 160×120, 4096 envs |
| Rendering FPS (high-res) | 300-500 | TBD | @ 640×480, 4096 envs |
| SR Inference (per image) | <2ms | TBD | GPU, batch=256 |
| End-to-end Latency | <15ms | TBD | Physics + render + SR |
| GPU Memory | <24GB | TBD | Single RTX 4090 |

### Quality Targets

| Metric | Target | Baseline | Notes |
|--------|--------|----------|-------|
| LPIPS (SR output) | <0.10 | 0.30 (DR) | vs ground truth |
| PSNR (SR output) | >28 dB | 22 dB (DR) | vs ground truth |
| SSIM (SR output) | >0.90 | 0.75 (DR) | vs ground truth |
| 3DGS LPIPS | <0.15 | - | Single view vs GT |

### Scalability Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Parallel Environments | 4096 | Single GPU |
| Training Throughput | 10k samples/hr | VLA policy training |
| Asset Library Size | 20+ objects | Phase 3 goal |
| Scene Diversity | 1000+ variants | Procedural generation |

---

## Getting Started

### Quick Start (5 minutes)

```bash
# 1. Clone and navigate
cd /home/ununtu/metabot-workspace/mugs

# 2. Read essential docs
cat README.md
cat TODO.md | head -50

# 3. Check project status
cat .context/MEMORY.md

# 4. Access shared memory
mm search "MuGS"
mm list 5f2b6991-35d1-4e00-85a7-516beb8b48c6
```

### Installation (15 minutes)

See `docs/guides/INSTALLATION.md` for detailed instructions.

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install package
pip install -e .

# 3. Download assets and models
python scripts/data_collection/download_assets.py --all

# 4. Verify installation
python -c "import mugs; print(mugs.__version__)"
```

### Run First Example (5 minutes)

```bash
# Render a single 3DGS view
python examples/basic/render_single_view.py

# Benchmark batched rendering
python examples/basic/render_batched.py --num-envs 4096
```

### Start Development

```bash
# 1. Create feature branch
git checkout -b phase-1-gsplat-poc

# 2. Read technical design for current phase
cat docs/design/TECHNICAL_DESIGN.md | less

# 3. Start with first task in TODO.md
cat TODO.md | grep -A 20 "Phase 1"

# 4. Update TODO.md as you complete tasks
```

---

## Support & Resources

### Documentation
- **Technical Design**: `docs/design/TECHNICAL_DESIGN.md`
- **Research Ideas**: `docs/RESEARCH_IDEAS.md`
- **Asset Guide**: `docs/guides/ASSET_ACQUISITION.md`
- **Installation Guide**: `docs/guides/INSTALLATION.md`

### Memory Systems
- **Metamemory Folder**: `5f2b6991-35d1-4e00-85a7-516beb8b48c6`
- **Auto-Memory**: `~/.claude/projects/-home-ununtu-metabot-workspace/memory/`
- **Repo Context**: `.context/MEMORY.md`

### External Links
- gsplat: https://github.com/nerfstudio-project/gsplat
- MuJoCo: https://mujoco.org/
- SwinIR: https://github.com/JingyunLiang/SwinIR
- Objaverse: https://objaverse.allenai.org/

---

**Last Updated**: 2026-05-02  
**Next Milestone**: Phase 1 - gsplat PoC (2 weeks)
