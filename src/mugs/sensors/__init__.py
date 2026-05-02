"""
MuGS Sensors: Photorealistic rendering sensors for MuJoCo.

Supports both standalone usage and mjlab integration (auto-detected).
"""

from .base import SensorBase, is_mjlab_available
from .gaussian_sensor import GaussianSensor, GaussianSensorConfig

__all__ = [
    'SensorBase',
    'GaussianSensor',
    'GaussianSensorConfig',
    'is_mjlab_available',
]
