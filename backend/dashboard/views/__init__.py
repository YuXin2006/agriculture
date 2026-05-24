from .ai import AIAnalysisAPIView
from .alarm import AlarmDetailAPIView, AlarmListCreateAPIView
from .base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView
from .data_analysis import DataAnalysisDetailAPIView, DataAnalysisListCreateAPIView
from .devices import DeviceGPSAPIView, DeviceNodeDetailAPIView, DeviceNodeListCreateAPIView
from .env_monitor import EnvMonitorDetailAPIView, EnvMonitorListCreateAPIView
from .overview import OverviewAPIView, SensorDataDetailAPIView, SensorDataListCreateAPIView
from .soil_monitor import SoilMonitorDetailAPIView, SoilMonitorListCreateAPIView

__all__ = [
    "OverviewAPIView",
    "SensorDataListCreateAPIView",
    "SensorDataDetailAPIView",
    "DeviceNodeListCreateAPIView",
    "DeviceNodeDetailAPIView",
    "DeviceGPSAPIView",
    "EnvMonitorListCreateAPIView",
    "EnvMonitorDetailAPIView",
    "SoilMonitorListCreateAPIView",
    "SoilMonitorDetailAPIView",
    "DataAnalysisListCreateAPIView",
    "DataAnalysisDetailAPIView",
    "AlarmListCreateAPIView",
    "AlarmDetailAPIView",
    "AIAnalysisAPIView",
    "ModelCRUDListCreateAPIView",
    "ModelCRUDDetailAPIView",
]
