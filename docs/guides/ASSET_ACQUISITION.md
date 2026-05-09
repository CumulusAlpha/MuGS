# Asset Acquisition Guide

This guide covers how to obtain 3D Gaussian Splatting (3DGS) models and pre-trained super-resolution models for MuGS.

> 想自己拍摄场景而不是下载？请直接看 **[GS_DATA_COLLECTION.md](GS_DATA_COLLECTION.md)** —— 拍摄 → COLMAP → 3DGS 训练 → 落地 MuGS 的完整教程。

**Last Updated**: 2026-05-02

---

## Table of Contents

1. [Overview](#overview)
2. [3DGS Object Models](#3dgs-object-models)
3. [Pre-trained SR Models](#pre-trained-sr-models)
4. [Automated Download](#automated-download)
5. [Manual Acquisition](#manual-acquisition)
6. [Asset Validation](#asset-validation)
7. [Custom Asset Creation](#custom-asset-creation)

---

## Overview

### Asset Requirements

MuGS requires two types of assets:

1. **3DGS Object Models** (`.ply` files)
   - Photorealistic 3D Gaussian Splatting models
   - Individual objects (not full scenes)
   - File size: 1-50 MB per object
   - Target: 20+ objects across 4 categories

2. **Pre-trained Models** (`.pt` / `.pth` files)
   - Super-resolution model (SwinIR-light)
   - Perceptual loss networks (LPIPS/VGG)
   - Optional: Alternative SR models

### Quick Start

**Easiest method** - Use automated download script:
```bash
cd /home/ununtu/metabot-workspace/mugs
python scripts/data_collection/download_assets.py --all
```

This will download:
- 5 sample 3DGS objects
- SwinIR-light pretrained model
- LPIPS/VGG networks
- Example scenes

**Estimated download**: ~500 MB, ~10 minutes

---

## 3DGS Object Models

### Option 1: Objaverse-3DGS (Recommended)

**Source**: https://objaverse.allenai.org/  
**Format**: 3D meshes → convert to 3DGS  
**License**: Varies (check per-object)  
**Size**: 800k+ objects available

#### What to Download

We recommend starting with these categories:

| Category | Object Types | Count | Priority |
|----------|-------------|-------|----------|
| Kitchen | Mugs, plates, bowls, utensils | 5 | High |
| Tools | Hammers, screwdrivers, wrenches | 5 | High |
| Containers | Boxes, bins, bottles | 5 | Medium |
| Misc | Toys, electronics, books | 5 | Low |

#### Automated Download

```bash
# Download kitchen objects (5 samples)
python scripts/data_collection/download_assets.py \
    --source objaverse \
    --category kitchen \
    --count 5

# Download all recommended objects (20 total)
python scripts/data_collection/download_assets.py \
    --source objaverse \
    --preset recommended
```

#### What the Script Does

1. Downloads meshes from Objaverse
2. Converts to 3DGS using `nerfstudio` pipeline:
   - Generates multi-view images (COLMAP)
   - Trains 3DGS model (~5 min per object)
   - Exports to `.ply` format
3. Creates metadata `.yaml` files
4. Organizes into `assets/objects/{category}/`

**Requirements**:
- GPU with 8GB+ VRAM
- ~2 hours for 20 objects (can parallelize)

---

### Option 2: Pre-converted 3DGS Models

Several sources provide pre-trained 3DGS models:

#### A. NeRF Synthetic Dataset
**Source**: https://github.com/bmild/nerf  
**Objects**: Chair, drums, ficus, hotdog, lego, materials, mic, ship  
**License**: Apache-2.0  
**Quality**: High (synthetic, clean backgrounds)

**Download**:
```bash
python scripts/data_collection/download_assets.py \
    --source nerf-synthetic \
    --objects chair,lego,hotdog,drums
```

#### B. Replica Dataset
**Source**: https://github.com/facebookresearch/Replica-Dataset  
**Content**: Indoor scenes (extractable objects)  
**License**: CC BY-NC 4.0 (research only)  
**Quality**: Photorealistic, indoor environments

**Download**:
```bash
python scripts/data_collection/download_assets.py \
    --source replica \
    --extract-objects
```

**Note**: Requires scene segmentation to extract individual objects.

#### C. Google Scanned Objects
**Source**: https://github.com/google-research-datasets/scanned-objects  
**Objects**: 1000+ everyday objects  
**License**: CC BY 4.0  
**Quality**: Real scans, high quality

**Download**:
```bash
python scripts/data_collection/download_assets.py \
    --source google-scanned \
    --category household \
    --count 10
```

**Conversion needed**: Meshes → 3DGS (script handles this)

---

### Option 3: Community 3DGS Models

#### Hugging Face Collections

Several Hugging Face repos host 3DGS models:

```bash
# Example: Download from HF
python scripts/data_collection/download_assets.py \
    --source huggingface \
    --repo "username/3dgs-objects" \
    --subset kitchen
```

**Recommended repos** (check availability):
- `szymanowiczs/splat-objects`
- `camenduru/3dgs-collection`
- Community-contributed collections

#### Manual Download Template

If downloading manually:

1. **Download `.ply` file**
2. **Create metadata YAML**:
```yaml
# assets/configs/kitchen/mug_blue.yaml
name: "mug_blue"
category: "kitchen"
size: [0.08, 0.08, 0.10]  # meters (width, depth, height)
mass: 0.3  # kg
source: "objaverse"
object_id: "abc123def456"
captured: "2024-03-15"
license: "CC-BY-4.0"
notes: "Blue ceramic mug, handle on right"
```

3. **Place files**:
```
assets/
  objects/
    kitchen/
      mug_blue.ply          ← Gaussian model
  configs/
    kitchen/
      mug_blue.yaml         ← Metadata
```

---

## Pre-trained SR Models

### SwinIR-light (Recommended)

**Purpose**: Super-resolution backbone  
**Source**: https://github.com/JingyunLiang/SwinIR  
**License**: Apache-2.0  
**Model Size**: ~900K parameters (~3.5 MB)

#### Download Pre-trained Weights

```bash
# Automated download
python scripts/data_collection/download_assets.py \
    --models swinir-light

# Manual download
wget https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth \
    -O models/sr/swinir_light_pretrained.pth
```

**What we'll use**:
- Pre-trained on real-world images (x4 upscaling)
- Fine-tune on our sim data (Stage 1 renders → ground truth)

---

### Alternative SR Models

#### Real-ESRGAN
**Source**: https://github.com/xinntao/Real-ESRGAN  
**License**: BSD-3  
**Quality**: Excellent for real photos, may need adaptation

```bash
python scripts/data_collection/download_assets.py \
    --models realesrgan
```

#### EDSR / RCAN
Classical SR models, lighter weight:
```bash
python scripts/data_collection/download_assets.py \
    --models edsr
```

---

### Perceptual Loss Networks

#### LPIPS (Learned Perceptual Image Patch Similarity)

**Purpose**: Perceptual loss for SR training  
**Source**: https://github.com/richzhang/PerceptualSimilarity  
**License**: BSD-2

```bash
# Automatically downloaded when installing lpips package
pip install lpips
```

**Models included**:
- VGG backbone (default)
- AlexNet backbone
- SqueezeNet backbone

**Our choice**: VGG (best performance)

---

## Automated Download

### Using `download_assets.py`

The main download script handles all asset acquisition.

#### Basic Usage

```bash
# Download everything (recommended for first setup)
python scripts/data_collection/download_assets.py --all

# Download only 3DGS objects
python scripts/data_collection/download_assets.py \
    --objects-only \
    --count 5

# Download only pre-trained models
python scripts/data_collection/download_assets.py --models-only

# Download specific category
python scripts/data_collection/download_assets.py \
    --category kitchen \
    --count 10
```

#### Advanced Options

```bash
# Specify output directory
python scripts/data_collection/download_assets.py \
    --all \
    --output-dir /path/to/assets

# Parallel downloads (faster)
python scripts/data_collection/download_assets.py \
    --all \
    --workers 4

# Dry run (preview what will be downloaded)
python scripts/data_collection/download_assets.py \
    --all \
    --dry-run

# Resume interrupted download
python scripts/data_collection/download_assets.py \
    --all \
    --resume
```

#### Preset Configurations

```bash
# Quick start: minimal assets for testing
python scripts/data_collection/download_assets.py --preset quick
# → 3 objects, 1 SR model, ~50 MB, ~2 minutes

# Recommended: balanced set for development
python scripts/data_collection/download_assets.py --preset recommended
# → 20 objects, 2 SR models, ~500 MB, ~10 minutes

# Full: comprehensive asset library
python scripts/data_collection/download_assets.py --preset full
# → 50+ objects, all SR models, ~2 GB, ~30 minutes
```

---

## Manual Acquisition

### Step-by-Step: Download Sample Objects

#### 1. NeRF Synthetic Lego

```bash
# Download
mkdir -p /tmp/nerf_data
cd /tmp/nerf_data
wget http://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/nerf_synthetic.zip
unzip nerf_synthetic.zip

# Convert to 3DGS (requires nerfstudio)
ns-train splatfacto --data nerf_synthetic/lego

# Export PLY
ns-export gaussian-splat \
    --load-config outputs/lego/splatfacto/.../config.yml \
    --output-dir /home/ununtu/metabot-workspace/mugs/assets/objects/misc/

# Rename
mv lego.ply /home/ununtu/metabot-workspace/mugs/assets/objects/misc/lego_bricks.ply
```

#### 2. Create Metadata

```bash
cat > /home/ununtu/metabot-workspace/mugs/assets/configs/misc/lego_bricks.yaml <<EOF
name: "lego_bricks"
category: "misc"
size: [0.15, 0.15, 0.10]
mass: 0.05
source: "nerf-synthetic"
captured: "2020-08-01"
license: "Apache-2.0"
notes: "Colorful lego bulldozer toy"
EOF
```

---

### Step-by-Step: Download SwinIR

```bash
# Create model directory
mkdir -p /home/ununtu/metabot-workspace/mugs/models/sr

# Download pre-trained checkpoint
wget https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth \
    -O /home/ununtu/metabot-workspace/mugs/models/sr/swinir_light_x4.pth

# Verify download
python -c "
import torch
ckpt = torch.load('models/sr/swinir_light_x4.pth')
print(f'Model keys: {ckpt.keys()}')
print(f'Params: {ckpt[\"params\"] if \"params\" in ckpt else \"N/A\"}')
"
```

---

## Asset Validation

### Validate Downloaded Assets

After downloading, run validation:

```bash
python scripts/data_collection/validate_assets.py

# Expected output:
# ✅ Found 5 objects in assets/objects/
# ✅ All objects have metadata YAML
# ✅ All PLY files are valid
# ✅ SwinIR checkpoint found and loadable
# ✅ LPIPS model available
```

### Visual Inspection

Generate preview images:

```bash
python scripts/evaluation/visualize_assets.py \
    --output-dir /tmp/asset_previews

# Opens browser with grid of rendered objects
```

### Quality Checks

Automated quality validation:

```bash
python scripts/evaluation/check_asset_quality.py

# Checks:
# - File size (1-50 MB typical)
# - Number of Gaussians (10k-1M typical)
# - Bounding box size (reasonable for robotics)
# - Rendering quality (LPIPS < 0.15)
```

---

## Custom Asset Creation

### Creating Your Own 3DGS Objects

If you want to capture custom objects:

#### Requirements
- Camera (smartphone OK, DSLR better)
- Object with good texture (avoid reflective/transparent)
- Turntable or fixed camera + rotate object
- 50-200 images from different viewpoints

#### Pipeline: Images → 3DGS

**Option A: Using Nerfstudio (Recommended)**

```bash
# 1. Organize images
mkdir -p /tmp/my_object/images
# Place images in /tmp/my_object/images/

# 2. Run COLMAP (structure from motion)
ns-process-data images \
    --data /tmp/my_object/images \
    --output-dir /tmp/my_object/processed

# 3. Train 3DGS
ns-train splatfacto \
    --data /tmp/my_object/processed \
    --output-dir /tmp/my_object/output

# 4. Export PLY
ns-export gaussian-splat \
    --load-config /tmp/my_object/output/.../config.yml \
    --output-dir assets/objects/custom/

# 5. Create metadata YAML (see template above)
```

**Option B: Using Original 3DGS Code**

```bash
# 1. Run COLMAP
python scripts/data_collection/run_colmap.py \
    --images /tmp/my_object/images \
    --output /tmp/my_object/colmap

# 2. Train 3DGS
python train.py \
    --source_path /tmp/my_object/colmap \
    --model_path /tmp/my_object/gaussian_output

# 3. Export to PLY
python export.py \
    --model_path /tmp/my_object/gaussian_output \
    --output assets/objects/custom/my_object.ply
```

#### Capture Tips

1. **Lighting**: Even, diffuse lighting (avoid harsh shadows)
2. **Background**: Plain, non-textured background
3. **Coverage**: 360° coverage, multiple elevations
4. **Overlap**: 70-80% overlap between consecutive images
5. **Focus**: Sharp focus, avoid motion blur
6. **Resolution**: 1080p minimum, 4K better

---

## Asset Organization

### Directory Structure

```
assets/
├── objects/                     # 3DGS object models
│   ├── kitchen/
│   │   ├── mug_blue.ply        # 3DGS model (5-20 MB)
│   │   ├── plate_white.ply
│   │   └── ...
│   ├── tools/
│   │   ├── hammer.ply
│   │   └── ...
│   ├── containers/
│   └── misc/
│
├── configs/                     # Metadata YAML files
│   ├── kitchen/
│   │   ├── mug_blue.yaml       # Metadata
│   │   └── plate_white.yaml
│   └── ...
│
└── scenes/                      # Pre-generated scenes
    ├── tabletop/
    ├── kitchen/
    └── floor/

models/
├── sr/                          # Super-resolution models
│   ├── swinir_light_x4.pth     # Pretrained SwinIR
│   ├── sim_aware_sr.pt         # Our fine-tuned model (Phase 4)
│   └── realesrgan_x4.pth       # Alternative
│
└── perception/                  # Perceptual loss models
    └── lpips_vgg.pth            # Auto-downloaded by lpips package
```

---

## Troubleshooting

### Common Issues

#### 1. Download Fails / Slow

**Problem**: Network timeout or slow download

**Solution**:
```bash
# Use mirror (if available)
python scripts/data_collection/download_assets.py \
    --all \
    --mirror tsinghua  # or aliyun for China

# Resume interrupted download
python scripts/data_collection/download_assets.py \
    --all \
    --resume
```

#### 2. COLMAP Fails

**Problem**: Structure-from-motion reconstruction fails

**Solution**:
- Check image quality (blur, lighting)
- Ensure 70%+ overlap between images
- Try different COLMAP settings:
```bash
python scripts/data_collection/run_colmap.py \
    --images /path/to/images \
    --matcher exhaustive  # slower but more robust
```

#### 3. 3DGS Training Out of Memory

**Problem**: GPU OOM during 3DGS training

**Solution**:
```bash
# Reduce image resolution
ns-train splatfacto \
    --data /path/to/data \
    --pipeline.datamanager.downscale_factor 2

# Or reduce batch size
ns-train splatfacto \
    --data /path/to/data \
    --pipeline.model.num_points 100000  # default: 500000
```

#### 4. PLY File Too Large

**Problem**: 3DGS model file >100 MB

**Solution**:
```bash
# Prune low-opacity Gaussians
python scripts/data_collection/prune_gaussians.py \
    --input assets/objects/demo_kitchen/mug.ply \
    --output assets/objects/demo_kitchen/mug_pruned.ply \
    --opacity-threshold 0.1  # Remove α < 0.1

# Typical size reduction: 50-70%
```

---

## Next Steps

After acquiring assets:

1. **Validate**: Run `validate_assets.py`
2. **Visualize**: Check `visualize_assets.py` output
3. **Test Rendering**: Try `examples/basic/render_single_view.py`
4. **Start Phase 1**: Begin gsplat PoC (see `TODO.md`)

---

## References

- **3D Gaussian Splatting**: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/
- **Nerfstudio**: https://docs.nerf.studio/
- **SwinIR**: https://github.com/JingyunLiang/SwinIR
- **Objaverse**: https://objaverse.allenai.org/
- **COLMAP**: https://colmap.github.io/

---

**Last Updated**: 2026-05-02  
**Next Update**: After Phase 1 (add actual download links)
