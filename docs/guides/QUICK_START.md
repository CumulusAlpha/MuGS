# MuGS Quick Start Guide

Get up and running with MuGS in 15 minutes.

**Last Updated**: 2026-05-02

---

## Prerequisites

- ✅ Linux system (Ubuntu 20.04+ recommended)
- ✅ NVIDIA GPU with 8GB+ VRAM
- ✅ CUDA 11.8 or 12.1 installed
- ✅ Python 3.10 or 3.11

**Not ready?** See [Installation Guide](INSTALLATION.md) for detailed setup.

---

## 5-Minute Setup

### 1. Navigate to Project

```bash
cd /home/ununtu/metabot-workspace/mugs
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install MuGS

```bash
pip install -e ".[all]"
```

⏱️ **Time**: ~5-8 minutes (downloads and compiles dependencies)

### 4. Download Sample Assets

```bash
python scripts/data_collection/download_assets.py --preset quick
```

⏱️ **Time**: ~2 minutes (~50 MB download)

### 5. Verify Installation

```bash
python -c "import mugs; print(f'✅ MuGS {mugs.__version__} ready!')"
```

**Expected output**: `✅ MuGS 0.1.0 ready!`

---

## Your First Rendering (2 minutes)

### Example 1: Render a Single Object

```bash
python examples/basic/render_single_view.py
```

**What this does**:
1. Loads a sample 3DGS object (`assets/objects/kitchen/mug_blue.ply`)
2. Renders from a single camera viewpoint
3. Saves image to `outputs/render_single_view.png`

**Expected output**:
```
Loading 3DGS model: mug_blue.ply
Rendering from camera at (0, 0, 1)...
✅ Rendered in 12.3ms
💾 Saved to: outputs/render_single_view.png
```

### Example 2: Batched Rendering

```bash
python examples/basic/render_batched.py --num-envs 64
```

**What this does**:
1. Creates 64 parallel cameras
2. Renders the same object from 64 different viewpoints
3. Measures FPS and throughput

**Expected output**:
```
Batched rendering: 64 cameras
Resolution: 160x120
✅ Rendered 64 views in 45.2ms
📊 Throughput: 1416 FPS
```

### Example 3: MuJoCo Integration (Phase 2+)

```bash
# Available after Phase 2 implementation
python examples/basic/mujoco_integration.py
```

---

## Project Structure Tour (3 minutes)

### Essential Files

```bash
mugs/
├── README.md              ← Start here: Project overview
├── TODO.md                ← Current phase tasks
├── PROJECT_OVERVIEW.md    ← Comprehensive project reference
├── .context/MEMORY.md     ← Project memory & context
│
├── docs/
│   ├── guides/
│   │   ├── QUICK_START.md      ← This file
│   │   ├── INSTALLATION.md     ← Detailed setup guide
│   │   └── ASSET_ACQUISITION.md ← How to get assets
│   ├── design/
│   │   └── TECHNICAL_DESIGN.md  ← 8000+ word implementation guide
│   └── RESEARCH_IDEAS.md        ← Research questions & experiments
│
├── src/mugs/              ← Main Python package
│   ├── sensors/           ← GaussianSensor (Phase 2)
│   ├── sr_models/         ← Super-resolution (Phase 4)
│   ├── scene_gen/         ← Procedural scenes (Phase 3)
│   └── utils/             ← Utilities
│
├── examples/              ← Runnable examples
│   ├── basic/
│   │   ├── render_single_view.py
│   │   ├── render_batched.py
│   │   └── mujoco_integration.py
│   └── advanced/
│
├── scripts/               ← Utility scripts
│   ├── data_collection/
│   │   └── download_assets.py
│   └── evaluation/
│       └── check_environment.py
│
└── assets/                ← 3DGS models & scenes
    ├── objects/           ← PLY files
    │   ├── kitchen/
    │   ├── tools/
    │   └── ...
    └── configs/           ← Metadata YAML
```

### Quick Navigation Commands

```bash
# Check current phase
cat TODO.md | head -50

# Read project context
cat .context/MEMORY.md

# See technical design for current phase
cat docs/design/TECHNICAL_DESIGN.md | less

# List available assets
tree assets/objects/ -L 2

# Check development status
git log --oneline -10
```

---

## Understanding the Pipeline (5 minutes)

### The Two-Stage Architecture

```
Physics (MuJoCo) → Stage 1 (3DGS) → Stage 2 (SR) → VLA Policy
     ↓                 ↓                ↓              ↓
  Camera Poses    Low-res render   High-res image   Actions
  (SE(3))         160×120          640×480
                  5000 FPS         +2ms latency
```

### Key Components

#### 1. **GaussianSensor** (Phase 2)
- Renders 3DGS models from camera poses
- Batched rendering: 4096 parallel cameras
- Output: Low-resolution RGB images (160×120)

```python
from mugs.sensors import GaussianSensor, GaussianSensorCfg

# Create sensor
config = GaussianSensorCfg(
    resolution=(160, 120),
    num_cameras=4096,
    asset_path="assets/objects/kitchen/mug_blue.ply"
)
sensor = GaussianSensor(config)

# Render from camera poses
images = sensor.update(camera_poses)  # Shape: (4096, 160, 120, 3)
```

#### 2. **SimAwareSR** (Phase 4)
- Super-resolution: 160×120 → 640×480
- Learns simulation-specific features
- Inference: <2ms per image

```python
from mugs.sr_models import SimAwareSR

# Load pre-trained model
sr_model = SimAwareSR.from_pretrained("models/sr/sim_aware_sr.pt")

# Upscale
low_res = images  # (N, 160, 120, 3)
high_res = sr_model(low_res)  # (N, 640, 480, 3)
```

#### 3. **SceneGenerator** (Phase 3)
- Procedurally generates diverse scenes
- Physics-valid object placement
- Export scene configurations

```python
from mugs.scene_gen import SceneGenerator, SceneTemplate

# Create generator
generator = SceneGenerator(template=SceneTemplate.TABLETOP)

# Generate scene
scene = generator.generate(num_objects=5)
scene.export("assets/scenes/tabletop/scene_001.h5")
```

---

## Development Workflow

### Starting a New Phase

```bash
# 1. Check TODO.md for current phase
cat TODO.md | grep -A 30 "Phase 1"

# 2. Create feature branch
git checkout -b phase-1-gsplat-poc

# 3. Read technical design for this phase
cat docs/design/TECHNICAL_DESIGN.md | grep -A 100 "Phase 1"

# 4. Implement according to design
# ... (write code)

# 5. Update TODO.md as you complete tasks
# Mark items as [x] when done

# 6. Commit changes
git add .
git commit -m "feat(sensors): implement GaussianSensor core"

# 7. Run tests
pytest tests/unit/test_sensors.py
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_transforms.py

# Run with coverage
pytest --cov=src/mugs --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

---

## Common Tasks

### Adding a New 3DGS Object

```bash
# 1. Place PLY file
cp /path/to/object.ply assets/objects/kitchen/

# 2. Create metadata
cat > assets/configs/kitchen/object.yaml <<EOF
name: "object"
category: "kitchen"
size: [0.10, 0.10, 0.15]  # meters [x, y, z]
mass: 0.4  # kg
source: "custom"
license: "CC-BY-4.0"
EOF

# 3. Verify
python scripts/evaluation/check_asset_quality.py --object kitchen/object
```

### Benchmarking Rendering

```bash
# Benchmark single-view rendering
python scripts/evaluation/benchmark_rendering.py \
    --mode single \
    --resolution 640 480

# Benchmark batched rendering
python scripts/evaluation/benchmark_rendering.py \
    --mode batched \
    --num-envs 4096 \
    --resolution 160 120
```

### Training SR Model (Phase 4)

```bash
# 1. Generate training data
python scripts/data_collection/generate_sr_dataset.py \
    --num-samples 10000 \
    --output data/sr_training/

# 2. Train model
python scripts/training/train_sr.py \
    --config configs/sr/sim_aware_sr.yaml \
    --data data/sr_training/ \
    --output models/sr/

# 3. Evaluate
python scripts/evaluation/eval_sr.py \
    --model models/sr/sim_aware_sr.pt \
    --test-data data/sr_training/test/
```

---

## Accessing Project Memory

MuGS uses multiple memory systems for cross-session context:

### 1. Metamemory (Shared Knowledge)

```bash
# Search for MuGS documents
mm search "MuGS"

# List all project documents
mm list 5f2b6991-35d1-4e00-85a7-516beb8b48c6

# Get specific document
mm get <doc_id>
```

### 2. Auto-Memory (Workspace Memory)

```bash
# Read memory files
cat ~/.claude/projects/-home-ununtu-metabot-workspace/memory/project_mjlab_3dgs_vla.md
cat ~/.claude/projects/-home-ununtu-metabot-workspace/memory/reference_mjlab_3dgs_vla.md
```

### 3. Repository Context

```bash
# Read in-repo context
cat .context/MEMORY.md
```

---

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Rendering FPS (low-res) | 5000-8000 | `benchmark_rendering.py --mode batched` |
| SR Latency | <2ms | `benchmark_sr.py --batch-size 256` |
| Image Quality (LPIPS) | <0.10 | `eval_sr.py --metric lpips` |
| End-to-end Latency | <15ms | `benchmark_pipeline.py` |

---

## Troubleshooting

### Quick Diagnostics

```bash
# Check environment
python scripts/evaluation/check_environment.py

# Verify GPU
nvidia-smi

# Test import
python -c "import mugs, torch, gsplat; print('✅ All imports OK')"

# Check assets
ls -lh assets/objects/kitchen/
```

### Common Issues

#### "CUDA out of memory"
```bash
# Reduce batch size
# Edit config file: num_envs: 4096 → 2048

# Or free GPU memory
nvidia-smi  # Find process PIDs
sudo kill -9 <PID>
```

#### "No module named 'mugs'"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install -e .
```

#### "Assets not found"
```bash
# Re-download assets
python scripts/data_collection/download_assets.py --preset quick --resume
```

---

## Next Steps

After completing this quick start:

1. ✅ **Read TODO.md**: Check Phase 1 tasks
2. ✅ **Read TECHNICAL_DESIGN.md**: Understand implementation details
3. ✅ **Start Phase 1**: Begin gsplat PoC
4. ✅ **Run Examples**: Experiment with basic scripts

---

## Learning Resources

### Documentation
- **Technical Design**: `docs/design/TECHNICAL_DESIGN.md` - Complete implementation guide
- **Research Ideas**: `docs/RESEARCH_IDEAS.md` - Research questions & experiments
- **Asset Guide**: `docs/guides/ASSET_ACQUISITION.md` - How to obtain assets
- **Project Overview**: `PROJECT_OVERVIEW.md` - Comprehensive reference

### External Resources
- **gsplat Documentation**: https://github.com/nerfstudio-project/gsplat
- **MuJoCo Docs**: https://mujoco.readthedocs.io/
- **SwinIR Paper**: https://arxiv.org/abs/2108.10257
- **3DGS Paper**: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/

---

## Getting Help

1. Check documentation (this file, INSTALLATION.md, TECHNICAL_DESIGN.md)
2. Search `.context/MEMORY.md` for project-specific context
3. Query metamemory: `mm search "MuGS <topic>"`
4. Review TODO.md for phase-specific guidance

---

**Ready to build?** 🚀

Start with Phase 1: `cat TODO.md | grep -A 50 "Phase 1"`

---

**Last Updated**: 2026-05-02  
**For**: MuGS v0.1.0
