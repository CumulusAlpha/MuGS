"""
GaussianSensorMjlab Real Test with 16 Environments

Tests batch rendering with real mjlab.Environment.

Author: MuGS Team
Date: 2026-05-02
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import torch

# Add r2v2-loco mjlab to path
MJLAB_PATH = "/home/ununtu/metabot-workspace/r2v2-loco/third_party/mjlab/src"
sys.path.insert(0, MJLAB_PATH)


def test_mjlab_import():
    """Test if mjlab can be imported."""
    print("=" * 70)
    print("Test 1: Import mjlab")
    print("=" * 70)

    try:
        from mjlab.sensor import Sensor, SensorCfg
        import mujoco_warp as mjwarp
        print("✅ mjlab imported successfully")
        print(f"   Sensor: {Sensor}")
        print(f"   mjwarp: {mjwarp}")
        return True
    except ImportError as e:
        print(f"❌ mjlab import failed: {e}")
        print(f"   Tried path: {MJLAB_PATH}")
        return False


def create_test_scene():
    """Create simple MuJoCo scene for testing."""

    scene_xml = """
    <mujoco model="test_scene">
      <compiler angle="radian"/>
      <option timestep="0.002" gravity="0 0 -9.81"/>

      <visual>
        <global offwidth="640" offheight="480"/>
      </visual>

      <asset>
        <texture type="skybox" builtin="gradient" rgb1="0.3 0.5 0.7" rgb2="0 0 0"
                 width="512" height="512"/>
      </asset>

      <worldbody>
        <!-- Floor -->
        <geom name="floor" type="plane" size="5 5 0.1" rgba="0.2 0.3 0.4 1"/>
        <light pos="0 0 3" dir="0 0 -1"/>

        <!-- Simple robot arm -->
        <body name="robot_base" pos="0 0 0.5">
          <geom name="base_link" type="cylinder" size="0.1 0.05" rgba="0.8 0.3 0.2 1"/>

          <body name="arm" pos="0 0 0.05">
            <joint name="shoulder" type="hinge" axis="0 0 1" range="-3.14 3.14" damping="0.5"/>
            <geom name="arm_link" type="capsule" size="0.03" fromto="0 0 0 0.3 0 0"
                  rgba="0.2 0.6 0.8 1"/>

            <body name="forearm" pos="0.3 0 0">
              <joint name="elbow" type="hinge" axis="0 0 1" range="-2.0 2.0" damping="0.3"/>
              <geom name="forearm_link" type="capsule" size="0.025" fromto="0 0 0 0.25 0 0"
                    rgba="0.2 0.8 0.6 1"/>
            </body>
          </body>
        </body>

        <!-- Camera will be added by sensor.edit_spec() -->
      </worldbody>

      <actuator>
        <position name="act_shoulder" joint="shoulder" kp="10"/>
        <position name="act_elbow" joint="elbow" kp="10"/>
      </actuator>
    </mujoco>
    """

    return scene_xml


def test_sensor_creation():
    """Test GaussianSensorMjlab creation."""
    print("\n" + "=" * 70)
    print("Test 2: Sensor Creation")
    print("=" * 70)

    from mugs.sensors.gaussian_sensor_mjlab import GaussianSensorMjlabCfg

    cfg = GaussianSensorMjlabCfg(
        name="test_sensor",
        width=320,
        height=240,
        camera_name=None,  # Create new camera
        pos=(0.8, -0.6, 1.0),
        quat=(1.0, 0.0, 0.0, 0.0),
        fov_degrees=60.0,
        background_ply_path=None,  # No 3DGS for simple test
        render_mode="mujoco_only",  # Start with MuJoCo-only
        robot_geom_names=['base_link', 'arm_link', 'forearm_link'],
        cache_background=False,
        return_components=True,
    )

    print(f"Config created:")
    print(f"  Name: {cfg.name}")
    print(f"  Resolution: {cfg.width}×{cfg.height}")
    print(f"  Mode: {cfg.render_mode}")

    try:
        sensor = cfg.build()
        print(f"✅ Sensor built: {sensor.__class__.__name__}")
        print(f"   requires_sensor_context: {sensor.requires_sensor_context}")
        return sensor
    except Exception as e:
        print(f"❌ Sensor build failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_environment_integration(sensor):
    """Test sensor with mjlab.Environment."""
    print("\n" + "=" * 70)
    print("Test 3: Environment Integration")
    print("=" * 70)

    try:
        from mjlab import Environment
        print("✅ Environment imported")
    except ImportError as e:
        print(f"❌ Environment import failed: {e}")
        print("   This is expected - mjlab.Environment may not be available")
        print("   Testing with manual scene construction instead...")
        return test_manual_integration(sensor)

    # Create scene XML
    scene_xml = create_test_scene()

    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(scene_xml)
        scene_path = f.name

    print(f"Scene XML: {scene_path}")

    try:
        # Create environment with 16 parallel instances
        env = Environment(
            model_path=scene_path,
            sensors=[sensor],
            num_envs=16,
            device="cuda",
        )

        print(f"✅ Environment created:")
        print(f"   num_envs: {env.num_envs}")
        print(f"   sensors: {list(env.sensors.keys())}")

        # Reset and get observations
        obs = env.reset()

        print(f"\n✅ Observations:")
        for sensor_name, data in obs.items():
            print(f"   {sensor_name}:")
            if hasattr(data, 'rgb'):
                print(f"     rgb: {data.rgb.shape} {data.rgb.dtype}")
            if hasattr(data, 'foreground'):
                print(f"     foreground: {data.foreground.shape if data.foreground is not None else None}")
            if hasattr(data, 'mask'):
                print(f"     mask: {data.mask.shape if data.mask is not None else None}")

        # Test one step
        actions = torch.zeros((16, 2), device="cuda")  # 2 actuators
        obs, reward, done, info = env.step(actions)

        print(f"\n✅ Step executed:")
        print(f"   obs keys: {list(obs.keys())}")
        print(f"   reward: {reward.shape}")
        print(f"   done: {done.shape}")

        return True

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manual_integration(sensor):
    """Test sensor with manual MuJoCo scene construction."""
    print("\n" + "=" * 70)
    print("Test 3b: Manual Scene Construction")
    print("=" * 70)

    import mujoco

    # Create scene spec
    scene_xml = create_test_scene()
    spec = mujoco.MjSpec()
    spec.from_string(scene_xml)

    print("✅ Scene spec created")

    # Call sensor.edit_spec()
    try:
        sensor.edit_spec(spec, {})
        print("✅ sensor.edit_spec() executed")

        # Check if camera was added
        cam = spec.camera(sensor.cfg.name)
        if cam is not None:
            print(f"✅ Camera '{sensor.cfg.name}' added to spec")
        else:
            print(f"❌ Camera '{sensor.cfg.name}' not found in spec")

    except Exception as e:
        print(f"❌ edit_spec() failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Compile model
    try:
        mj_model = spec.compile()
        print(f"✅ Model compiled: {mj_model.nq} DOF")

        # Create single data (not batch)
        mj_data = mujoco.MjData(mj_model)

        # Try to call initialize (will fail without mjwarp, but we can see the error)
        print("\n⚠️  Would call sensor.initialize() here, but needs mjwarp.Model/Data")
        print("   This requires full mjlab.Environment setup")

        return True

    except Exception as e:
        print(f"❌ Model compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""

    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "GaussianSensorMjlab Real Test (16 envs)" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Test 1: Import
    mjlab_ok = test_mjlab_import()

    if not mjlab_ok:
        print("\n" + "=" * 70)
        print("⚠️  mjlab not available - testing with fallback mode")
        print("=" * 70)

    # Test 2: Sensor creation
    sensor = test_sensor_creation()

    if sensor is None:
        print("\n❌ Tests stopped - sensor creation failed")
        return

    # Test 3: Integration
    if mjlab_ok:
        test_environment_integration(sensor)
    else:
        test_manual_integration(sensor)

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("""
Tests completed. Results:
- mjlab import: Check above
- Sensor creation: Check above
- Integration: Check above

Next steps if tests pass:
1. Implement _get_camera_poses_batch() using mjwarp
2. Test with real 3DGS background
3. Scale to 4096 environments
4. Benchmark performance

If tests fail:
1. Check mjlab installation
2. Verify mujoco_warp availability
3. Check CUDA/torch compatibility
    """)


if __name__ == "__main__":
    import os
    os.environ['TORCH_CUDA_ARCH_LIST'] = '8.6'
    main()
