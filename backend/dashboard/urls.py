from django.urls import path

from .views import (
    AIAnalysisAPIView,
    AlarmDetailAPIView,
    AlarmListCreateAPIView,
    ChatAPIView,
    ChatClearAPIView,
    ChatHistoryAPIView,
    ChatStreamAPIView,
    DataAnalysisDetailAPIView,
    DataAnalysisListCreateAPIView,
    DeviceGPSAPIView,
    DeviceNodeDetailAPIView,
    DeviceNodeListCreateAPIView,
    EnvMonitorDetailAPIView,
    EnvMonitorListCreateAPIView,
    OverviewAPIView,
    SensorDataDetailAPIView,
    SensorDataListCreateAPIView,
    SoilMonitorDetailAPIView,
    SoilMonitorListCreateAPIView,
)


urlpatterns = [
    # 总览（兼容旧接口）
    path("overview/", OverviewAPIView.as_view(), name="overview"),
    path("sensors/", SensorDataListCreateAPIView.as_view(), name="sensor-list-create"),
    path("sensors/<int:pk>/", SensorDataDetailAPIView.as_view(), name="sensor-detail"),
    # 设备管理
    path("devices/", DeviceNodeListCreateAPIView.as_view(), name="device-list-create"),
    path("devices/<int:pk>/", DeviceNodeDetailAPIView.as_view(), name="device-detail"),
    path("devices/<int:pk>/gps/", DeviceGPSAPIView.as_view(), name="device-gps"),
    # 环境监测
    path("env-monitor/", EnvMonitorListCreateAPIView.as_view(), name="env-monitor-list"),
    path("env-monitor/<int:pk>/", EnvMonitorDetailAPIView.as_view(), name="env-monitor-detail"),
    # 土壤监测
    path("soil-monitor/", SoilMonitorListCreateAPIView.as_view(), name="soil-monitor-list"),
    path("soil-monitor/<int:pk>/", SoilMonitorDetailAPIView.as_view(), name="soil-monitor-detail"),
    # 数据分析
    #path("data-analysis/", DataAnalysisListCreateAPIView.as_view(), name="data-analysis-list"),
    #path("data-analysis/<int:pk>/", DataAnalysisDetailAPIView.as_view(), name="data-analysis-detail"),
    # 告警记录
    path("alarm/", AlarmListCreateAPIView.as_view(), name="alarm-list"),
    path("alarm/<int:pk>/", AlarmDetailAPIView.as_view(), name="alarm-detail"),
    # AI 分析
    #path("ai/analysis/", AIAnalysisAPIView.as_view(), name="ai-analysis"),
    # AI 聊天
    path("chat/", ChatAPIView.as_view(), name="chat"),
    path("chat/stream/", ChatStreamAPIView.as_view(), name="chat-stream"),
    path("chat/history/", ChatHistoryAPIView.as_view(), name="chat-history"),
    path("chat/clear/", ChatClearAPIView.as_view(), name="chat-clear"),
]
