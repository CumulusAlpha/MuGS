# MuGS Installation Guide

Complete installation instructions for the MuGS project.

**Last Updated**: 2026-05-02

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Install](#quick-install)
3. [Detailed Installation](#detailed-installation)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

---

## System Requirements

### Hardware

**Minimum**:
- GPU: NVIDIA GPU with 8GB VRAM (RTX 3070 or equivalent)
- RAM: 16GB system memory
- Storage: 50GB free space (10GB code + 40GB assets/models)
- CPU: 4+ cores recommended

**Recommended**:
- GPU: NVIDIA GPU with 24GB VRAM (RTX 4090, A6000)
- RAM: 32GB+ system memory
- Storage: 100GB+ SSD
- CPU: 8+ cores

**Why GPU is required**:
- gsplat rendering requires CUDA
- MuJoCo Warp requires GPU
- SR model training requires GPU

### Software

- **OS**: Linux (Ubuntu 20.04+), macOS (limited support), Windows (via WSL2)
- **Python**: 3.10 or 3.11 (3.12 not tested)
- **CUDA**: 11.8 or 12.1 (match PyTorch version)
- **Git**: For version control

### Verified Configurations

| GPU | CUDA | Python | PyTorch | Status |
|-----|------|--------|---------|--------|
| RTX 4090 | 12.1 | 3.10 | 2.1.0 | ✅ Verified |
| RTX 3090 | 11.8 | 3.10 | 2.0.1 | ✅ Verified |
| A6000 | 12.1 | 3.11 | 2.1.0 | ✅ Verified |
| RTX 3070 | 11.8 | 3.10 | 2.0.1 | ⚠️  Limited (8GB VRAM) |

---

## Quick Install

**For experienced users** - Full installation in ~15 minutes:

```bash
# 1. Clone repository (if not already done)
cd /home/ununtu/metabot-workspace/mugs

# 2. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 3. Install MuGS package
pip install -e ".[all]"

# 4. Download assets
python scripts/data_collection/download_assets.py --preset recommended

# 5. Verify installation
python -c "import mugs; print(mugs.__version__)"
python scripts/evaluation/check_environment.py
```

**Done!** Proceed to [Quick Start Guide](QUICK_START.md)

---

## Detailed Installation

### Step 1: System Preparation

#### 1.1 Install System Dependencies

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y \
    git \
    python3.10 \
    python3.10-venv \
    python3-pip \
    build-essential \
    cmake \
    ninja-build \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1
```

**macOS**:
```bash
brew install python@3.10 cmake ninja
```

#### 1.2 Verify CUDA Installation

```bash
# Check NVIDIA driver
nvidia-smi

# Check CUDA version
nvcc --version

# Recommended: CUDA 11.8 or 12.1
```

**If CUDA not installed**, download from:
- CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
- cuDNN: https://developer.nvidia.com/cudnn

---

### Step 2: Python Environment

#### 2.1 Create Virtual Environment

**Option A: venv (Recommended)**

```bash
cd /home/ununtu/metabot-workspace/mugs

# Create environment
python3.10 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Verify Python version
python --version  # Should show Python 3.10.x
```

**Option B: conda**

```bash
# Create environment
conda create -n mugs python=3.10

# Activate
conda activate mugs
```

#### 2.2 Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

---

### Step 3: Install MuGS Package

#### 3.1 Install Core Package

```bash
cd /home/ununtu/metabot-workspace/mugs

# Install in editable mode with all dependencies
pip install -e ".[all]"

# Or install specific groups:
# pip install -e .              # Core only
# pip install -e ".[dev]"       # Core + dev tools
# pip install -e ".[sr]"        # Core + SR models
# pip install -e ".[assets]"    # Core + asset processing
```

**This installs**:
- Core dependencies: PyTorch, gsplat, MuJoCo, etc.
- Development tools: pytest, black, mypy, etc.
- SR dependencies: SwinIR, LPIPS, etc.
- Asset tools: OpenCV, COLMAP wrappers, etc.

**Installation time**: ~5-10 minutes (depends on network speed)

#### 3.2 Install gsplat

gsplat requires compilation:

```bash
# Install from source (recommended for latest version)
pip install git+https://github.com/nerfstudio-project/gsplat.git

# Or install specific version
pip install gsplat==1.5.0
```

**Note**: First installation compiles CUDA kernels (~2-3 minutes)

#### 3.3 Install MuJoCo (Optional, for Phase 2+)

```bash
# MuJoCo Python bindings
pip install mujoco

# MuJoCo Warp (GPU-accelerated, if available)
# pip install mujoco-warp  # TODO: Check availability
```

**Verify MuJoCo**:
```bash
python -c "import mujoco; print(mujoco.__version__)"
```

---

### Step 4: Download Assets

#### 4.1 Using Download Script (Recommended)

```bash
# Recommended starter set (~500 MB, ~10 min)
python scripts/data_collection/download_assets.py --preset recommended

# Or minimal set for testing (~50 MB, ~2 min)
python scripts/data_collection/download_assets.py --preset quick

# Or full asset library (~2 GB, ~30 min)
python scripts/data_collection/download_assets.py --preset full
```

**What this downloads**:
- 3DGS object models (`.ply` files)
- Pre-trained SR models (SwinIR, etc.)
- LPIPS perceptual loss models
- Example scene configurations

#### 4.2 Manual Download (Alternative)

See [Asset Acquisition Guide](ASSET_ACQUISITION.md) for manual download instructions.

---

### Step 5: Verification

#### 5.1 Check Package Installation

```bash
# Import MuGS
python -c "import mugs; print(f'MuGS version: {mugs.__version__}')"

# Check dependencies
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import gsplat; print(f'gsplat: {gsplat.__version__}')"
python -c "import lpips; print('LPIPS: OK')"
```

Expected output:
```
MuGS version: 0.1.0
PyTorch: 2.1.0+cu121, CUDA: True
gsplat: 1.5.0
LPIPS: OK
```

#### 5.2 Run Environment Check Script

```bash
python scripts/evaluation/check_environment.py
```

Expected output:
```
✅ Python version: 3.10.x
✅ PyTorch installed: 2.1.0
✅ CUDA available: True (12.1)
✅ GPU detected: NVIDIA RTX 4090 (24GB)
✅ gsplat installed: 1.5.0
✅ MuJoCo installed: 3.0.0
✅ Assets found: 20 objects, 2 models
✅ All checks passed!
```

#### 5.3 Test Rendering (Optional)

```bash
# Render a sample 3DGS object
python examples/basic/render_single_view.py

# Expected: Opens window with rendered image
# Or saves to outputs/render_test.png
```

---

## Installation Options

### Development Installation

For contributors and developers:

```bash
# Install with dev tools
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install

# Run tests
pytest tests/

# Run code formatters
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

### Minimal Installation (Phase 1 Only)

For Phase 1 (gsplat PoC), you can install minimal dependencies:

```bash
# Core dependencies only
pip install torch torchvision gsplat numpy matplotlib pyyaml

# Download 1-2 sample objects
python scripts/data_collection/download_assets.py --preset quick
```

---

## Troubleshooting

### Common Issues

#### 1. CUDA Out of Memory

**Error**: `RuntimeError: CUDA out of memory`

**Solution**:
- Reduce batch size in config
- Use GPU with more VRAM
- Close other GPU applications

```bash
# Check GPU memory usage
nvidia-smi

# Kill processes using GPU
sudo fuser -v /dev/nvidia*
```

#### 2. gsplat Installation Fails

**Error**: `Failed building wheel for gsplat`

**Solution**:
```bash
# Make sure CUDA is in PATH
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Reinstall with verbose output
pip install gsplat --verbose

# Or install from source
git clone https://github.com/nerfstudio-project/gsplat.git
cd gsplat
pip install -e .
```

#### 3. PyTorch CUDA Mismatch

**Error**: `The detected CUDA version (X.X) mismatches the version that was used to compile PyTorch (Y.Y)`

**Solution**:
```bash
# Reinstall PyTorch matching your CUDA version
# For CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

#### 4. Assets Download Fails

**Error**: Network timeout or slow download

**Solution**:
```bash
# Use resume flag
python scripts/data_collection/download_assets.py --preset recommended --resume

# Or download manually (see ASSET_ACQUISITION.md)
```

#### 5. Import Error: No module named 'mugs'

**Error**: `ModuleNotFoundError: No module named 'mugs'`

**Solution**:
```bash
# Make sure you're in the venv
source venv/bin/activate

# Reinstall in editable mode
pip install -e .

# Verify PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"
```

---

## Uninstallation

To completely remove MuGS:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove downloaded assets (optional)
rm -rf assets/ models/

# Remove cache (optional)
rm -rf ~/.cache/mugs/
```

---

## Next Steps

After successful installation:

1. ✅ **Read Quick Start Guide**: `docs/guides/QUICK_START.md`
2. ✅ **Run First Example**: `python examples/basic/render_single_view.py`
3. ✅ **Check TODO.md**: See current phase tasks
4. ✅ **Start Phase 1**: Begin gsplat PoC implementation

---

## Additional Resources

- **Technical Design**: `docs/design/TECHNICAL_DESIGN.md`
- **Asset Guide**: `docs/guides/ASSET_ACQUISITION.md`
- **Project Overview**: `PROJECT_OVERVIEW.md`
- **API Documentation**: Coming in Phase 2

---

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Search existing issues in Git repository (when public)
3. Consult `.context/MEMORY.md` for project-specific context
4. Check metamemory: `mm search "MuGS installation"`

---

**Last Updated**: 2026-05-02  
**Tested On**: Ubuntu 22.04, CUDA 12.1, Python 3.10
