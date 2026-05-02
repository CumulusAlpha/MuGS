# MuGS_mjlab - MJLab Integration Package

MJLab integration for MuGS 3DGS rendering.

## Features

- ✅ GaussianSensor API for mjlab environments
- ✅ Automatic MuJoCo camera parameter extraction
- ✅ Hybrid MuJoCo + 3DGS rendering
- ✅ Batch rendering support

## Installation

```bash
# Install core package first
pip install mugs

# Then install mjlab extension  
pip install mugs-mjlab
```

## Quick Start

```python
from mjlab.envs import ManagerBasedRlEnv
from mugs_mjlab import GaussianSensorCfg

env_cfg = MyEnvCfg()
env_cfg.scene.sensors["rgb"] = GaussianSensorCfg(
    camera_name="camera1",
    resolution=(640, 480),
    scene_ply="kitchen.ply",
    mask_config="mask_config_kitchen.yaml"
)

env = ManagerBasedRlEnv(cfg=env_cfg)
obs, _ = env.reset()
# obs["rgb"]: (N_env, 640, 480, 3)
```

## Documentation

See [main docs](../../docs/) for detailed documentation.

## License

Apache 2.0
