"""
MuGS: MuJoCo Gaussian Splatting

A scalable, photorealistic Vision-Language-Action benchmark using 3D Gaussian
Splatting rendering with MuJoCo Warp physics simulation.
"""

__version__ = "0.1.0"

from mugs.sensors import GaussianSensor, GaussianSensorCfg

__all__ = [
    "GaussianSensor",
    "GaussianSensorCfg",
    "__version__",
]
