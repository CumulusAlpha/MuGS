# MuGS Assets

Small demonstration assets included in the repository for testing and examples.

## Directory Structure

```
assets/
├── configs/          # Sensor and mask configurations
│   └── mask_config_kitchen.yaml
├── objects/          # Individual 3DGS object assets
│   ├── demo_kitchen/ # Kitchen utensils (demo objects)
│   └── misc/         # Miscellaneous objects
└── scenes/           # Complete 3DGS scene compositions
    └── demo_kitchen/ # Kitchen countertop scene (12 objects)
```

## Usage

### Demo Objects

Located in `objects/demo_kitchen/` - simple 3DGS objects for testing:
- `bowl_green.ply` - Green bowl (115KB)
- `mug_blue.ply` - Blue mug (192KB)
- `plate_white.ply` - White plate (147KB)

### Demo Kitchen Scene

Located in `scenes/demo_kitchen/` - complete kitchen countertop scene with 12 objects:
- 12 individual PLY files (cups, plates, bowls, shakers, fruits)
- `kitchen_scene.json` - Scene composition metadata
- Total: ~6,180 Gaussians, 1.6MB

Load the scene in code:
```python
from pathlib import Path
import json

scene_dir = Path("assets/scenes/demo_kitchen")
scene_config = json.load(open(scene_dir / "kitchen_scene.json"))

for obj in scene_config["objects"]:
    ply_path = scene_dir / obj["file"]
    position = obj["position"]
    # Load and position object...
```

## Large Assets

For large pretrained scenes (INRIA kitchen, DISCOVERSE, etc.), see the `data/` directory:
- `data/pretrained/` - Downloaded pretrained 3DGS scenes
- `data/external/` - External datasets (DISCOVERSE, GS-Playground, etc.)

Download scripts: `scripts/download_external_assets.py`

## Asset Sources

All assets in this directory are synthetic/demo objects created for MuGS testing.

For research datasets and pretrained scenes, refer to:
- **INRIA Kitchen**: mip-NeRF 360 dataset (download via scripts)
- **DISCOVERSE**: [DISCOVERSE dataset](https://github.com/NGC4151/DISCOVERSE)
- **GS-Playground**: [gs-playground](https://github.com/YOUR_ORG/gs-playground)

## License

Demo assets in this directory are released under Apache-2.0 license.
External datasets have their own licenses - see respective sources.
