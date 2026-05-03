# MuGS API Reference

Complete API documentation for MuGS rendering system.

---

## Table of Contents

- [Core Rendering](#core-rendering)
  - [GaussianSensor](#gaussiansensor)
  - [GaussianSensorConfig](#gaussiansensorconfig)
- [Post-Processing](#post-processing)
  - [SuperResolution](#superresolution)
  - [SuperResolutionConfig](#superresolutionconfig)
- [Batch Rendering (mjlab)](#batch-rendering-mjlab)
  - [GaussianSensorMjlab](#gaussiansensormjlab)
  - [GaussianSensorMjlabCfg](#gaussiansensormjlabcfg)

---

## Core Rendering

### GaussianSensor

Main rendering class for standalone (single-environment) use.

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig
```

#### Constructor

```python
GaussianSensor(cfg: GaussianSensorConfig)
```

**Parameters:**
- `cfg` (`GaussianSensorConfig`): Sensor configuration

**Example:**
```python
sensor = GaussianSensor(GaussianSensorConfig(
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["link1", "link2", "gripper"],
))
```

#### Methods

##### `render()`

Render a single frame from MuJoCo simulation.

```python
render(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    camera_name: str,
    return_components: bool = False
) -> Union[np.ndarray, Dict[str, np.ndarray]]
```

**Parameters:**
- `model` (`mujoco.MjModel`): MuJoCo model
- `data` (`mujoco.MjData`): MuJoCo data (simulation state)
- `camera_name` (`str`): Name of the camera in MJCF
- `return_components` (`bool`, optional): If `True`, return dict with all components. Default: `False`

**Returns:**
- If `return_components=False`: `np.ndarray` of shape `(H, W, 3)`, dtype `uint8`
- If `return_components=True`: `Dict[str, np.ndarray]` with keys:
  - `'rgb'`: Final composited image `(H, W, 3)` uint8
  - `'foreground'`: MuJoCo-only render `(H, W, 3)` uint8
  - `'background'`: 3DGS-only render `(H, W, 3)` uint8
  - `'mask'`: Foreground mask `(H, W, 1)` uint8

**Example:**
```python
# Simple usage
rgb = sensor.render(model, data, "main_camera")

# With components
result = sensor.render(model, data, "main_camera", return_components=True)
rgb = result['rgb']
foreground = result['foreground']
background = result['background']
mask = result['mask']
```

---

### GaussianSensorConfig

Configuration dataclass for `GaussianSensor`.

```python
from mugs.sensors import GaussianSensorConfig
```

#### Fields

```python
@dataclass
class GaussianSensorConfig:
    # Resolution
    width: int = 640
    height: int = 480
    
    # 3DGS Background
    background_ply_path: Optional[Path] = None
    
    # Rendering mode
    render_mode: str = "hybrid"  # "hybrid" | "3dgs_only" | "mujoco_only"
    
    # Robot masking (choose one)
    robot_geom_names: List[str] = field(default_factory=list)
    robot_geom_ids: Optional[List[int]] = None
    robot_body_prefixes: List[str] = field(default_factory=list)
    
    # Background camera (optional)
    background_camera_json: Optional[Path] = None
    background_camera_idx: int = 0
    
    # Device
    device: str = "cuda"
```

**Field Descriptions:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | `int` | `640` | Output image width |
| `height` | `int` | `480` | Output image height |
| `background_ply_path` | `Path` | `None` | Path to 3DGS PLY file (required for `hybrid`/`3dgs_only` modes) |
| `render_mode` | `str` | `"hybrid"` | Rendering mode: `"hybrid"`, `"3dgs_only"`, or `"mujoco_only"` |
| `robot_geom_names` | `List[str]` | `[]` | List of geom names to include in foreground mask |
| `robot_geom_ids` | `List[int]` | `None` | Alternative: List of geom IDs (for unnamed geoms) |
| `robot_body_prefixes` | `List[str]` | `[]` | Alternative: Body name prefixes (e.g., `["robot/", "obj_"]`) |
| `background_camera_json` | `Path` | `None` | Path to COLMAP `cameras.json` (optional) |
| `background_camera_idx` | `int` | `0` | Index of camera in `cameras.json` |
| `device` | `str` | `"cuda"` | PyTorch device: `"cuda"` or `"cpu"` |

**Robot Masking Methods:**

Choose **one** of three methods to specify which geoms belong to the foreground:

1. **By geom names** (recommended for named geoms):
   ```python
   robot_geom_names=["panda_link0", "panda_link1", "gripper_finger1"]
   ```

2. **By geom IDs** (for unnamed geoms):
   ```python
   robot_geom_ids=[0, 1, 2, 5, 6]
   ```

3. **By body prefixes** (for namespaced scenes):
   ```python
   robot_body_prefixes=["robot/", "table/", "obj_"]
   ```

**Example:**
```python
config = GaussianSensorConfig(
    width=640,
    height=480,
    background_ply_path=Path("data/pretrained/kitchen/point_cloud.ply"),
    render_mode="hybrid",
    robot_geom_names=["link1", "link2", "gripper"],
    device="cuda",
)
```

---

## Post-Processing

### SuperResolution

AI upscaling module using Real-ESRGAN. Modular and optional.

```python
from mugs.postprocess import SuperResolution, SuperResolutionConfig
```

#### Constructor

```python
SuperResolution(cfg: SuperResolutionConfig)
```

**Parameters:**
- `cfg` (`SuperResolutionConfig`): Super-resolution configuration

**Example:**
```python
sr = SuperResolution(SuperResolutionConfig(
    model_name="RealESRGAN_x4plus",
    scale=4,
))
```

**Installation:**
```bash
pip install realesrgan basicsr
python scripts/download_sr_models.py --model RealESRGAN_x4plus
```

#### Methods

##### `upscale()`

Upscale a single image.

```python
upscale(
    image: np.ndarray,
    outscale: Optional[int] = None
) -> np.ndarray
```

**Parameters:**
- `image` (`np.ndarray`): Input image, shape `(H, W, 3)`, dtype `uint8`
- `outscale` (`int`, optional): Output scale factor (2 or 4). If `None`, uses config default.

**Returns:**
- `np.ndarray`: Upscaled image, shape `(H*scale, W*scale, 3)`, dtype `uint8`

**Example:**
```python
img_lr = sensor.render(model, data, "camera")  # 320×240
img_hr = sr.upscale(img_lr)                     # 1280×960
```

##### `batch_upscale()`

Upscale multiple images (with progress bar).

```python
batch_upscale(
    images: List[np.ndarray],
    outscale: Optional[int] = None,
    show_progress: bool = False
) -> List[np.ndarray]
```

**Parameters:**
- `images` (`List[np.ndarray]`): List of input images
- `outscale` (`int`, optional): Output scale factor
- `show_progress` (`bool`): Show tqdm progress bar

**Returns:**
- `List[np.ndarray]`: List of upscaled images

**Example:**
```python
imgs_lr = [sensor.render(model, data, "camera") for _ in range(100)]
imgs_hr = sr.batch_upscale(imgs_lr, show_progress=True)
```

---

### SuperResolutionConfig

Configuration dataclass for `SuperResolution`.

```python
from mugs.postprocess import SuperResolutionConfig
```

#### Fields

```python
@dataclass
class SuperResolutionConfig:
    model_name: str = "RealESRGAN_x4plus"
    scale: int = 4
    model_path: Optional[Path] = None
    device: str = "cuda"
    fp16: bool = True
    tile_size: int = 0
    tile_pad: int = 10
    pre_pad: int = 0
```

**Field Descriptions:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model_name` | `str` | `"RealESRGAN_x4plus"` | Model name: `"RealESRGAN_x4plus"`, `"RealESRNet_x4plus"`, `"RealESRGAN_x4plus_anime_6B"` |
| `scale` | `int` | `4` | Upscaling factor: `2` or `4` |
| `model_path` | `Path` | `None` | Custom model path (if `None`, uses default in `data/pretrained/sr/`) |
| `device` | `str` | `"cuda"` | Device: `"cuda"` or `"cpu"` |
| `fp16` | `bool` | `True` | Use FP16 for speed (GPU only) |
| `tile_size` | `int` | `0` | Tile size for large images (0 = no tiling) |
| `tile_pad` | `int` | `10` | Padding between tiles |
| `pre_pad` | `int` | `0` | Pre-padding before inference |

**Model Comparison:**

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `RealESRGAN_x4plus` | 64 MB | Medium | ⭐⭐⭐⭐⭐ | General purpose (recommended) |
| `RealESRNet_x4plus` | 64 MB | Fast | ⭐⭐⭐⭐ | Faster inference |
| `RealESRGAN_x4plus_anime_6B` | 17 MB | Fast | ⭐⭐⭐⭐ | Anime/cartoon images |

**Example:**
```python
config = SuperResolutionConfig(
    model_name="RealESRGAN_x4plus",
    scale=4,
    device="cuda",
    fp16=True,
)
```

**For large images (4K+):**
```python
config = SuperResolutionConfig(
    tile_size=512,  # Process in tiles to save VRAM
    tile_pad=10,
)
```

---

## Batch Rendering (mjlab)

For parallel multi-environment rendering using `mjlab`.

### GaussianSensorMjlab

mjlab-compatible sensor for batch rendering.

```python
from mugs.sensors import GaussianSensorMjlab, GaussianSensorMjlabCfg
```

#### Constructor

```python
GaussianSensorMjlab(
    cfg: GaussianSensorMjlabCfg,
    model: mujoco.MjModel,
    num_envs: int
)
```

**Parameters:**
- `cfg` (`GaussianSensorMjlabCfg`): Sensor configuration
- `model` (`mujoco.MjModel`): MuJoCo model
- `num_envs` (`int`): Number of parallel environments

#### Methods

##### `forward()`

Render a batch of frames.

```python
forward(data: mujoco.MjData) -> torch.Tensor
```

**Parameters:**
- `data` (`mujoco.MjData`): Batched MuJoCo data (shape: `(num_envs, ...)`)

**Returns:**
- `torch.Tensor`: Batch of images, shape `(num_envs, H, W, 3)`, dtype `uint8`

**Example:**
```python
from mjlab import Environment

env = Environment(cfg, num_envs=8)
env.add_sensor(GaussianSensorMjlab(sensor_cfg, env.model, env.num_envs))

obs = env.reset()
images = obs['gaussian_camera']  # (8, H, W, 3)
```

---

### GaussianSensorMjlabCfg

Configuration for `GaussianSensorMjlab` (extends `GaussianSensorConfig`).

```python
from mugs.sensors import GaussianSensorMjlabCfg
```

#### Fields

```python
@dataclass
class GaussianSensorMjlabCfg(GaussianSensorConfig):
    name: str = "gaussian_camera"  # Sensor name in observation dict
    camera_name: str = "main_camera"  # MuJoCo camera name
```

**Additional fields:**
- `name`: Key in observation dict (e.g., `obs[name]`)
- `camera_name`: MuJoCo camera name to render from

**Example:**
```python
cfg = GaussianSensorMjlabCfg(
    name="wrist_camera",
    camera_name="wrist_cam",
    width=320,
    height=240,
    background_ply_path=Path("data/pretrained/kitchen/point_cloud.ply"),
    render_mode="hybrid",
    robot_geom_names=["link1", "link2"],
)
```

---

## Complete Usage Examples

### Standalone Rendering

```python
import mujoco
from mugs.sensors import GaussianSensor, GaussianSensorConfig

# Load scene
model = mujoco.MjModel.from_xml_path("scene.xml")
data = mujoco.MjData(model)

# Create sensor
sensor = GaussianSensor(GaussianSensorConfig(
    width=640,
    height=480,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["base", "link1", "link2", "gripper"],
))

# Simulation loop
for step in range(100):
    mujoco.mj_step(model, data)
    rgb = sensor.render(model, data, "main_camera")
    # Save or display rgb
```

### Batch Rendering

```python
from mjlab import Environment
from mugs.sensors import GaussianSensorMjlab, GaussianSensorMjlabCfg

# Environment config
env_cfg = EnvironmentConfig(...)

# Sensor config
sensor_cfg = GaussianSensorMjlabCfg(
    name="camera",
    camera_name="main_camera",
    width=320,
    height=240,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["link1", "link2"],
)

# Create environment
env = Environment(env_cfg, num_envs=16)
env.add_sensor(GaussianSensorMjlab(sensor_cfg, env.model, env.num_envs))

# Training loop
obs = env.reset()
for step in range(1000):
    action = policy(obs)
    obs = env.step(action)
    images = obs['camera']  # (16, 240, 320, 3)
```

### With Super-Resolution

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig
from mugs.postprocess import SuperResolution, SuperResolutionConfig

# Low-res sensor
sensor = GaussianSensor(GaussianSensorConfig(
    width=320,
    height=240,
    background_ply_path="data/pretrained/kitchen/point_cloud.ply",
    render_mode="hybrid",
    robot_geom_names=["link1", "link2"],
))

# Super-resolution
sr = SuperResolution(SuperResolutionConfig(
    model_name="RealESRGAN_x4plus",
    scale=4,
))

# Render + upscale
for step in range(100):
    mujoco.mj_step(model, data)
    img_lr = sensor.render(model, data, "camera")  # 320×240
    img_hr = sr.upscale(img_lr)                     # 1280×960
    # Use img_hr for evaluation/visualization
```

---

## See Also

- **[API Quick Start](API_QUICKSTART.md)** - Beginner-friendly guide (中文)
- **[Super-Resolution Guide](SUPER_RESOLUTION.md)** - Detailed SR documentation
- **[Examples](../examples/)** - Complete working examples
- **[Design Document](design/DESIGN.md)** - System architecture
