"""
Base sensor interface for MuGS.

Provides compatibility layer for mjlab integration while maintaining standalone functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np


# Try to import mjlab, fall back to our own base if not available
try:
    from mjlab.sensors import Sensor as MjlabSensor
    MJLAB_AVAILABLE = True
    BaseSensor = MjlabSensor
    print("[MuGS] mjlab detected - using mjlab.Sensor base class")
except ImportError:
    MJLAB_AVAILABLE = False
    BaseSensor = ABC
    print("[MuGS] mjlab not found - using standalone mode")


class SensorBase(BaseSensor):
    """
    Base class for MuGS sensors.

    - If mjlab is installed: inherits from mjlab.Sensor
    - If mjlab is not installed: standalone ABC implementation

    This allows GaussianSensor to work both standalone and as part of mjlab ecosystem.
    """

    if not MJLAB_AVAILABLE:
        # Standalone mode: define our own interface

        @abstractmethod
        def render(self, *args, **kwargs) -> np.ndarray:
            """
            Render sensor observation.

            Returns:
                RGB image as numpy array (H, W, 3) uint8
            """
            pass

        def get_observation_space(self) -> Dict[str, Any]:
            """
            Get observation space specification.

            For mjlab compatibility, should return dict with:
                - shape: tuple
                - dtype: numpy dtype
                - low/high: optional bounds
            """
            return {
                'shape': (self.height, self.width, 3),
                'dtype': np.uint8,
                'low': 0,
                'high': 255,
            }

        @property
        def width(self) -> int:
            """Sensor width in pixels."""
            raise NotImplementedError

        @property
        def height(self) -> int:
            """Sensor height in pixels."""
            raise NotImplementedError

    # Methods available in both modes

    def get_info(self) -> Dict[str, Any]:
        """Get sensor metadata and statistics."""
        return {
            'type': self.__class__.__name__,
            'resolution': (self.width, self.height),
            'mjlab_mode': MJLAB_AVAILABLE,
        }


def is_mjlab_available() -> bool:
    """Check if mjlab is available."""
    return MJLAB_AVAILABLE
