# MuGS - Core Rendering Package

High-performance 3D Gaussian Splatting rendering engine.

## Features

- ✅ Platform-agnostic 3DGS rendering
- ✅ Flexible mask configuration system  
- ✅ YAML-based scene configuration
- ✅ GPU-accelerated rendering (gsplat)
- ✅ Hybrid rendering support

## Installation

```bash
pip install mugs
```

## Quick Start

```python
from mugs import MaskConfig
from mugs.rendering import load_ply_gaussians

# Load 3DGS scene
gaussians = load_ply_gaussians("scene.ply")

# Load mask configuration
config = MaskConfig.from_yaml("mask_config.yaml")
```

## Documentation

See [main docs](../../docs/) for detailed documentation.

## License

Apache 2.0
