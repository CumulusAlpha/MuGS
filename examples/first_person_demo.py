#!/usr/bin/env python3
"""
First-Person Gripper Demo with 3DGS Background

展示第一人称视角的机器人夹爪面对桌面抓取场景：
- 背景：kitchen.ply（照片级真实感）
- 前景：MuJoCo 物理物体 + 夹爪
- 视角：手腕第一人称

快速演示 MuGS 的核心价值：粗糙的 MuJoCo 背景 → 照片级 3DGS 背景
"""

import mujoco
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mugs.sensors import GaussianSensor, GaussianSensorConfig


def main():
    print("=" * 80)
    print("First-Person Gripper Demo")
    print("=" * 80)

    # Paths
    scene_path = Path(__file__).parent.parent / "scenes" / "first_person_kitchen.xml"
    ply_path = Path(__file__).parent.parent / "data" / "pretrained" / "kitchen" / "point_cloud" / "iteration_30000" / "point_cloud.ply"
    output_dir = Path(__file__).parent.parent / "outputs" / "first_person_demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not ply_path.exists():
        print(f"❌ Background model not found: {ply_path}")
        print("   Run: python scripts/download_pretrained_models.py")
        return

    print(f"✅ Scene: {scene_path.name}")
    print(f"✅ Background: {ply_path}")

    # Load MuJoCo scene
    model = mujoco.MjModel.from_xml_path(str(scene_path))
    data = mujoco.MjData(model)

    # Robot geoms (gripper parts)
    robot_geoms = ['gripper_base', 'gripper_left', 'gripper_right']

    print(f"✅ Robot geoms: {robot_geoms}")

    # Create sensor with 3DGS background
    print("\n" + "=" * 80)
    print("Creating GaussianSensor...")
    print("=" * 80)

    config = GaussianSensorConfig(
        width=640,
        height=480,
        background_ply_path=ply_path,
        render_mode="hybrid",
        robot_geom_names=robot_geoms,
    )
    sensor = GaussianSensor(config)

    print("✅ Sensor created")

    # Render different modes
    print("\n" + "=" * 80)
    print("Rendering comparisons...")
    print("=" * 80)

    results = {}

    # Load camera 117 parameters from kitchen.ply
    import json
    cam_params_path = Path(__file__).parent.parent / "data" / "pretrained" / "kitchen" / "cameras.json"
    with open(cam_params_path) as f:
        cameras = json.load(f)
    cam117 = cameras[117]  # Use camera 117 that looks at tabletop

    print(f"  Using Camera 117 from kitchen.ply training set")
    print(f"    Position: {cam117['position']}")

    # 1. Hybrid mode (our result)
    print("  [1/3] Hybrid (3DGS background + MuJoCo foreground)...")
    sensor.cfg.render_mode = "hybrid"
    result_hybrid = sensor.render(model, data, "wrist_cam", return_components=True, camera_params=cam117)
    results['hybrid'] = result_hybrid

    # 2. MuJoCo only (baseline) - use same camera params
    print("  [2/3] MuJoCo only (baseline)...")
    sensor.cfg.render_mode = "mujoco_only"
    result_mujoco = sensor.render(model, data, "wrist_cam", camera_params=cam117)
    results['mujoco'] = {'rgb': result_mujoco}  # Wrap as dict

    # 3. 3DGS only (background) - use same camera params
    print("  [3/3] 3DGS only (background)...")
    sensor.cfg.render_mode = "3dgs_only"
    result_3dgs = sensor.render(model, data, "wrist_cam", camera_params=cam117)
    results['3dgs'] = {'rgb': result_3dgs}  # Wrap as dict

    # Visualization
    print("\n" + "=" * 80)
    print("Generating visualization...")
    print("=" * 80)

    fig = plt.figure(figsize=(20, 12))

    # Row 1: Comparison
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(results['mujoco']['rgb'])
    ax1.set_title('MuJoCo Only (Baseline)\n粗糙的仿真背景', fontsize=14, fontweight='bold')
    ax1.axis('off')

    ax2 = plt.subplot(2, 3, 2)
    ax2.imshow(results['3dgs']['rgb'])
    ax2.set_title('3DGS Only (Background)\n照片级真实背景', fontsize=14, fontweight='bold')
    ax2.axis('off')

    ax3 = plt.subplot(2, 3, 3)
    ax3.imshow(results['hybrid']['rgb'])
    ax3.set_title('MuGS Hybrid (Our Result)\n真实背景 + 物理物体', fontsize=14, fontweight='bold', color='#d62728')
    ax3.axis('off')

    # Row 2: Components
    ax4 = plt.subplot(2, 3, 4)
    ax4.imshow(results['hybrid']['background'])
    ax4.set_title('Component: 3DGS Background', fontsize=12)
    ax4.axis('off')

    ax5 = plt.subplot(2, 3, 5)
    ax5.imshow(results['hybrid']['foreground'])
    ax5.set_title('Component: MuJoCo Foreground', fontsize=12)
    ax5.axis('off')

    ax6 = plt.subplot(2, 3, 6)
    ax6.imshow(results['hybrid']['mask'], cmap='gray')
    ax6.set_title('Component: Robot Mask', fontsize=12)
    ax6.axis('off')

    plt.suptitle('MuGS First-Person Demo: Robot Gripper Perspective',
                 fontsize=18, fontweight='bold', y=0.98)

    plt.tight_layout()

    # Save
    output_path = output_dir / "first_person_comparison.jpg"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")

    # Save individual images
    for name, result in results.items():
        img_path = output_dir / f"{name}.jpg"
        plt.imsave(img_path, result['rgb'])
        print(f"✅ Saved: {img_path}")

    # Stats
    print("\n" + "=" * 80)
    print("Statistics")
    print("=" * 80)

    mask = results['hybrid']['mask']
    robot_ratio = mask.mean()
    print(f"  Robot pixels: {robot_ratio*100:.2f}%")
    print(f"  Background pixels: {(1-robot_ratio)*100:.2f}%")
    print(f"  Image size: {results['hybrid']['rgb'].shape}")

    print("\n" + "=" * 80)
    print("✅ Demo complete!")
    print("=" * 80)
    print(f"\nOutputs saved to: {output_dir}")
    print("\nKey insight:")
    print("  左图（MuJoCo）: 粗糙的仿真背景")
    print("  右图（MuGS）:  照片级真实背景 + 同样的物理物体")
    print("  → 完美的 Sim2Real VLA 训练场景！")


if __name__ == "__main__":
    main()
