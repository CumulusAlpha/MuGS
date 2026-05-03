# Super-Resolution Guide

Add photorealistic detail to low-resolution renders using AI upscaling.

## Overview

MuGS supports optional super-resolution (SR) upscaling using Real-ESRGAN models. This allows you to:
- **Render at low resolution** (fast, 5000+ FPS)
- **Upscale to high resolution** (slower, ~100ms per frame)
- **Get photorealistic details** that look like real photos

## Quick Start

### 1. Install Dependencies

```bash
pip install realesrgan basicsr
```

### 2. Download Pretrained Models

```bash
# Download recommended model (64 MB)
python scripts/download_sr_models.py --model RealESRGAN_x4plus

# Or download all models
python scripts/download_sr_models.py --all
```

### 3. Use in Code

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig
from mugs.postprocess import SuperResolution, SuperResolutionConfig

# Step 1: Low-res rendering (fast)
sensor_config = GaussianSensorConfig(
    width=320,
    height=240,
    background_ply_path="data/pretrained/kitchen/point_cloud/iteration_30000/point_cloud.ply",
)
sensor = GaussianSensor(sensor_config)

# Step 2: Super-resolution upscaling (optional)
sr_config = SuperResolutionConfig(
    model_name="RealESRGAN_x4plus",
    scale=4,
)
sr = SuperResolution(sr_config)

# Render and upscale
img_lr = sensor.render(model, data, camera_name)  # 320×240
img_hr = sr.upscale(img_lr)                        # 1280×960
```

## Available Models

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **RealESRGAN_x4plus** | 64 MB | Medium | ⭐⭐⭐⭐⭐ | General purpose, best quality |
| **RealESRNet_x4plus** | 64 MB | Fast | ⭐⭐⭐⭐ | Faster inference, good quality |
| **RealESRGAN_x4plus_anime_6B** | 17 MB | Fast | ⭐⭐⭐⭐ | Anime/cartoon images |

Download with:
```bash
python scripts/download_sr_models.py --model MODEL_NAME
```

## Configuration Options

```python
from mugs.postprocess import SuperResolutionConfig

config = SuperResolutionConfig(
    model_name="RealESRGAN_x4plus",  # Model to use
    scale=4,                          # Upscaling factor (2 or 4)
    model_path=None,                  # Custom model path (optional)
    device="cuda",                    # "cuda" or "cpu"
    fp16=True,                        # FP16 for speed (GPU only)
    tile_size=0,                      # Tile size (0=no tiling, 512 for 4K+)
    tile_pad=10,                      # Padding between tiles
    pre_pad=0,                        # Pre-padding before inference
)
```

## Usage Patterns

### Pattern 1: Training (No SR)

```python
# Fast low-res rendering for RL training
sensor = GaussianSensor(GaussianSensorConfig(width=160, height=120))

for episode in range(1000):
    obs = sensor.render(model, data, camera_name)  # Fast!
    action = policy(obs)
    # ...
```

**FPS**: ~10,000 FPS (160×120)

### Pattern 2: Evaluation (With SR)

```python
from mugs.postprocess import SuperResolution, SuperResolutionConfig

# Render low-res, upscale for evaluation
sensor = GaussianSensor(GaussianSensorConfig(width=320, height=240))
sr = SuperResolution(SuperResolutionConfig())

for episode in eval_episodes:
    img_lr = sensor.render(model, data, camera_name)
    img_hr = sr.upscale(img_lr)  # High quality for video
    save_frame(img_hr)
```

**FPS**: ~10 FPS (320×240 → 1280×960)

### Pattern 3: Batch Processing

```python
# Render many frames, then batch upscale
imgs_lr = []
for step in range(100):
    imgs_lr.append(sensor.render(model, data, camera_name))

# Batch upscale (shows progress)
imgs_hr = sr.batch_upscale(imgs_lr, show_progress=True)
```

### Pattern 4: Conditional SR

```python
# Only upscale every N frames for video
sr = SuperResolution(SuperResolutionConfig())

for i, img_lr in enumerate(frames):
    if i % 10 == 0:  # Keyframes only
        img_hr = sr.upscale(img_lr)
    else:
        img_hr = simple_resize(img_lr)  # Cheap interpolation
```

## Performance

### Speed Comparison

| Resolution | Rendering | SR (4x) | Total | FPS |
|------------|-----------|---------|-------|-----|
| 160×120 | 0.1 ms | 50 ms | 50 ms | 20 |
| 320×240 | 0.2 ms | 100 ms | 100 ms | 10 |
| 640×480 | 0.2 ms | 200 ms | 200 ms | 5 |
| 1280×960 | 0.5 ms | - | 0.5 ms | 2000 |

**Recommendation**: 
- Training: 160×120 or 320×240, no SR
- Evaluation: 320×240 → 1280×960 with SR
- Videos: 640×480 → 2560×1920 with SR

### GPU Memory

| Model | VRAM | Max Resolution |
|-------|------|----------------|
| RealESRGAN_x4plus | ~2 GB | 1920×1080 input |
| RealESRGAN_x4plus (FP16) | ~1 GB | 1920×1080 input |
| RealESRGAN_x4plus (tiled) | ~500 MB | Unlimited |

For 4K+ images, use tiling:
```python
config = SuperResolutionConfig(
    tile_size=512,  # Process in 512×512 tiles
    tile_pad=10,
)
```

## Advanced Usage

### Custom Model Path

```python
config = SuperResolutionConfig(
    model_path=Path("/path/to/custom_model.pth"),
    scale=4,
)
```

### CPU Mode

```python
config = SuperResolutionConfig(
    device="cpu",
    fp16=False,  # CPU doesn't support FP16
)
# Much slower but works without GPU
```

### Different Scales

```python
# Upscale by 2x instead of 4x
img_2x = sr.upscale(img_lr, outscale=2)

# Upscale by 8x (apply 4x twice)
img_4x = sr.upscale(img_lr)
img_8x = sr.upscale(img_4x)
```

## Troubleshooting

### Model Not Found

**Error**:
```
FileNotFoundError: Model not found: data/pretrained/sr/RealESRGAN_x4plus.pth
```

**Solution**:
```bash
python scripts/download_sr_models.py --model RealESRGAN_x4plus
```

### Import Error

**Error**:
```
ImportError: Real-ESRGAN not installed
```

**Solution**:
```bash
pip install realesrgan basicsr
```

### Out of Memory

**Error**:
```
RuntimeError: CUDA out of memory
```

**Solutions**:
1. Use smaller input resolution
2. Enable tiling:
   ```python
   config = SuperResolutionConfig(tile_size=512)
   ```
3. Use CPU (slower):
   ```python
   config = SuperResolutionConfig(device="cpu", fp16=False)
   ```

### Slow Performance

**Check**:
- GPU being used? `config.device = "cuda"`
- FP16 enabled? `config.fp16 = True`
- Small batch instead of one-by-one? Use `batch_upscale()`

## Integration with MuGS Pipeline

### Full Pipeline Example

```python
import mujoco
import numpy as np
from pathlib import Path

from mugs.sensors import GaussianSensor, GaussianSensorConfig
from mugs.postprocess import SuperResolution, SuperResolutionConfig

# 1. Setup MuJoCo scene
model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# 2. Setup low-res renderer
sensor = GaussianSensor(GaussianSensorConfig(
    width=320,
    height=240,
    background_ply_path=Path("data/pretrained/kitchen/point_cloud/iteration_30000/point_cloud.ply"),
    render_mode="hybrid",
))

# 3. Setup super-resolution (optional)
USE_SR = True
if USE_SR:
    sr = SuperResolution(SuperResolutionConfig(
        model_name="RealESRGAN_x4plus",
        scale=4,
    ))

# 4. Simulation loop
for step in range(100):
    # Simulate
    mujoco.mj_step(model, data)
    
    # Render low-res
    img_lr = sensor.render(model, data, "main_camera")
    
    # Optionally upscale
    if USE_SR:
        img_hr = sr.upscale(img_lr)
        save_frame(img_hr)
    else:
        save_frame(img_lr)
```

## Comparison: With vs Without SR

### Input: 320×240 (MuGS Rendered)
- Clean geometry
- Correct lighting
- But pixelated

### Output: 1280×960 (Real-ESRGAN 4x)
- Sharp edges
- Realistic textures (wood grain, metal reflections)
- Photorealistic detail

### Quality Gain
- **Sharpness**: ⭐⭐⭐⭐⭐
- **Texture detail**: ⭐⭐⭐⭐⭐
- **Realism**: ⭐⭐⭐⭐⭐
- **Speed cost**: 50-200ms per frame

## Citation

If you use Real-ESRGAN in your research:

```bibtex
@inproceedings{wang2021realesrgan,
  title={Real-ESRGAN: Training Real-World Blind Super-Resolution with Pure Synthetic Data},
  author={Wang, Xintao and Xie, Liangbin and Dong, Chao and Shan, Ying},
  booktitle={International Conference on Computer Vision Workshops (ICCVW)},
  year={2021}
}
```

## See Also

- **Real-ESRGAN GitHub**: https://github.com/xinntao/Real-ESRGAN
- **MuGS Examples**: `examples/sr_pipeline_demo.py`
- **Download Script**: `scripts/download_sr_models.py`
