#!/usr/bin/env python3
"""End-to-end mjlab + MuGS GaussianSensor multi-env benchmark."""
import os
os.environ.setdefault("MUJOCO_GL", "egl")
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mugs/src"))

import torch
from mjlab.tasks.manipulation.config.yam import yam_lift_cube_env_cfg
from mjlab.envs import ManagerBasedRlEnv
from mugs_mjlab import GaussianSensorMjlabCfg

REPO = Path("/home/ununtu/metabot-workspace/mugs")
PLY = REPO / "data/pretrained/kitchen/point_cloud/iteration_30000/point_cloud.ply"
assert PLY.exists(), f"ply missing: {PLY}"

W, H = 160, 120

def build(num_envs, render_mode="hybrid"):
    cfg = yam_lift_cube_env_cfg(play=True)
    cfg.scene.num_envs = num_envs
    sensor_cfg = GaussianSensorMjlabCfg(
        name="gs_rgb",
        camera_name="robot/camera_d405",
        width=W, height=H,
        background_ply_path=str(PLY),
        render_mode=render_mode,
    )
    # attach sensor (mjlab scene.sensors is a tuple of SensorCfg)
    cfg.scene.sensors = cfg.scene.sensors + (sensor_cfg,)
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda")
    return env

def bench_one(num_envs, mode, n_steps=30, warmup=5):
    torch.cuda.empty_cache()
    env = build(num_envs, mode)
    try:
        obs, _ = env.reset()
        action = torch.zeros(env.action_space.shape, device='cuda')
        for _ in range(warmup):
            env.step(action)
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(n_steps):
            env.step(action)
        torch.cuda.synchronize()
        dt = (time.time() - t0) / n_steps
        peak = torch.cuda.max_memory_allocated() / 1e9
        torch.cuda.reset_peak_memory_stats()
        try: env.close()
        except: pass
        return dt, num_envs/dt, peak
    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
        try: env.close()
        except: pass
        torch.cuda.empty_cache()
        return None, None, str(e)[:200]

print(f"Device: {torch.cuda.get_device_name(0)}")
free_b, total_b = torch.cuda.mem_get_info()
print(f"Free/Total VRAM: {free_b/1e9:.1f}/{total_b/1e9:.1f} GB\n")

print("=" * 72)
print(f"mjlab YAM-lift + GaussianSensorMjlab @ {W}×{H}, render_mode=hybrid")
print("=" * 72)
print(f"{'envs':>6} | {'step latency':>13} | {'env-FPS':>10} | {'peak VRAM':>10}")
print("-" * 72)
for B in [1, 4, 16, 64, 256, 1024, 4096]:
    dt, fps, peak = bench_one(B, "hybrid")
    if dt is None:
        print(f"{B:>6} | ERR: {peak[:50]}")
    else:
        print(f"{B:>6} | {dt*1000:>10.2f} ms | {fps:>10,.0f} | {peak:>7.2f} GB")
