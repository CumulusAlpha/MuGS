# DISCOVERSE 3DGS scenes

How to fetch and render the DISCOVERSE indoor 3DGS captures used by the
multi-camera AndroidTwin demo (see [the showcase
section](../README.md#discoverse-3dgs-rooms--androidtwin-multi-cam-rollout)
of the top-level README).

No scenes are tracked in this repo — `assets/scenes/*.ply` is `.gitignore`d.
The download script is the only path.

## What you get

Four indoor 3DGS captures from the DISCOVERSE project:

| Scene                       | Description                          | Packed (HF) | Unpacked |
|-----------------------------|--------------------------------------|------------:|---------:|
| `lab3`                      | Robotics lab corner (cabinet, desk)  |    ~5.5 MB |   ~23 MB |
| `flower_table`              | Indoor scene with a flower table     |    ~7.9 MB |   ~33 MB |
| `discover_operation_studio` | Operation studio room                |    ~8.4 MB |   ~36 MB |
| `tsimf_library_0`           | Library reading area                 |     ~22 MB |   ~92 MB |

Source: [`tatp/DISCOVERSE-models`](https://huggingface.co/tatp/DISCOVERSE-models)
on Hugging Face, paths under `3dgs/scene/<name>/point_cloud.ply`.

## Why the unpack step

DISCOVERSE ships scenes in PlayCanvas **SuperSplat compressed** PLY format
(chunked uint32 packed fields), not the official 3DGS schema. MuGS's
`GaussianSensor` only consumes the unpacked layout (`x/y/z`, `f_dc_*`,
`scale_*`, `rot_*`, `opacity`), so the script runs
`decompress_supersplat.py` once per scene right after download.

## Quick start

```bash
# default: lab3 only
bash scripts/data_collection/download_discoverse_scenes.sh

# everything
bash scripts/data_collection/download_discoverse_scenes.sh --all

# pick a subset
bash scripts/data_collection/download_discoverse_scenes.sh lab3 flower_table
```

Outputs land in:

```
assets/scenes/discoverse/<scene>/point_cloud.ply          # packed (archival)
assets/scenes/discoverse_unpacked/<scene>/point_cloud.ply # unpacked (renderable)
```

Override with `--dst-root <dir>` or env `DISCOVERSE_SCENE_ROOT=…`. The
unpacked directory always appends `_unpacked` to the chosen root.

## Dependencies

- `curl` (or `wget`) for download.
- `python3` with `numpy` and `plyfile` for the decompressor.

## Render with MuGS

```python
from mugs.sensors import GaussianSensor, GaussianSensorConfig

cfg = GaussianSensorConfig(
    width=480,
    height=360,
    background_ply_path="assets/scenes/discoverse_unpacked/lab3/point_cloud.ply",
    render_mode="3dgs_only",   # or "hybrid" with a MuJoCo foreground
)
sensor = GaussianSensor(cfg)
```

Pair with `MuGSRecorder` (in the AndroidTwin repo) for a full
hybrid 3DGS + MuJoCo + MuJoCo-cam-tracking pipeline.

## Gotchas worth knowing once

1. **Don't render the packed PLY directly.** `GaussianSensor` will load it
   and silently render noise. Always go through the unpack step.
2. **Use `bbox.center` for xy, `percentile(z, 5)` for floor.** COLMAP
   leaves a small number of sub-floor splats that drag `bbox.min[2]` ~1 m
   below the actual floor; the 5th-percentile reading is robust. The
   median xy is biased toward the densest splat cluster (e.g. lab3
   `median_y=+0.72` vs `bbox_center_y=+0.20`) which can push virtual
   cameras outside the training-cam convex hull — use the bbox center.
3. **`gs_intrinsics ≠ MuJoCo intrinsics`.** Feed the GS scene's training
   focal length (lab3 ≈ 380 px at 480×360) to the renderer, not the
   MuJoCo camera's own `fx/fy`. A mismatch shows up as squashed or
   stretched backgrounds.
4. **GS coverage ≠ scene bbox.** Each capture only renders cleanly
   *inside the convex hull of the training cameras*. lab3's training
   cams are biased toward the GS `-X` half — virtual cameras placed in
   the `+X` half will render dim/blurry noise. Use AndroidTwin's
   `examples/dump_cam_params.py` to isolate a single camera's GS-only
   render before composing a full multi-cam rollout.
