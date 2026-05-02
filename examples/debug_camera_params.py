#!/usr/bin/env python3
"""Debug camera parameter extraction"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import mujoco
import numpy as np

# Load the quality comparison scene
exec(open('examples/quality_comparison_demo.py').read().split('def main()')[0])

scene_xml = create_pick_place_scene()
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
    f.write(scene_xml)
    scene_path = f.name

model = mujoco.MjModel.from_xml_path(scene_path)
data = mujoco.MjData(model)

# Set robot pose
data.qpos[0] = 0.3
data.qpos[1] = 0.5
data.qpos[2] = -0.8
data.qpos[3] = 0.2
data.qpos[4] = -0.015
data.qpos[5] = 0.015

mujoco.mj_forward(model, data)

# Get camera params
camera_name = "wrist_view"
camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)

print("=" * 80)
print(f"Camera: {camera_name} (ID: {camera_id})")
print("=" * 80)

# Position
pos = data.cam_xpos[camera_id]
print(f"\nPosition: [{pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}]")

# Rotation matrix
mat = data.cam_xmat[camera_id].reshape(3, 3)
print(f"\nRotation matrix:")
for i in range(3):
    print(f"  [{mat[i,0]:.6f}, {mat[i,1]:.6f}, {mat[i,2]:.6f}]")

# Camera forward direction (-Z in camera space)
forward = -mat[:, 2]
up = mat[:, 1]
right = mat[:, 0]
print(f"\nForward: [{forward[0]:.6f}, {forward[1]:.6f}, {forward[2]:.6f}]")
print(f"Up:      [{up[0]:.6f}, {up[1]:.6f}, {up[2]:.6f}]")
print(f"Right:   [{right[0]:.6f}, {right[1]:.6f}, {right[2]:.6f}]")

# FOV (in radians, affected by <compiler angle="radian"/>)
fov_y_radians = model.cam_fovy[camera_id]
fov_y_degrees = np.degrees(fov_y_radians)
print(f"\nFOV_y: {fov_y_degrees:.2f}° ({fov_y_radians:.4f} rad)")

# What the camera should be looking at (approximate)
look_point = pos + forward * 0.5  # 0.5m in front
print(f"\nLook point (0.5m ahead): [{look_point[0]:.6f}, {look_point[1]:.6f}, {look_point[2]:.6f}]")

# Compare with robot/objects positions
print("\n" + "=" * 80)
print("Objects in scene:")
print("=" * 80)

for name in ['robot_base', 'red_cube', 'blue_cylinder', 'green_sphere']:
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
    obj_pos = data.xpos[body_id]
    dist = np.linalg.norm(obj_pos - pos)
    to_obj = obj_pos - pos
    to_obj_norm = to_obj / np.linalg.norm(to_obj)
    dot = np.dot(to_obj_norm, forward)
    angle = np.degrees(np.arccos(np.clip(dot, -1, 1)))
    print(f"{name:20s}: pos=[{obj_pos[0]:.3f}, {obj_pos[1]:.3f}, {obj_pos[2]:.3f}]  dist={dist:.3f}m  angle={angle:.1f}°")

print("\n" + "=" * 80)
print("Camera should see:")
print("=" * 80)
print("Objects with angle < 30° are likely in view")
