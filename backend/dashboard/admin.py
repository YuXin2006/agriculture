from django.contrib import admin

from .models import (
    AlarmRecord,
    DataAnalysisReport,
    DeviceNode,
    EnvMonitorRecord,
    SensorData,
    SoilMonitorRecord,
)


@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ("id", "soil_moisture", "temperature", "co2", "light", "created_at")
    ordering = ("-created_at",)


@admin.register(DeviceNode)
class DeviceNodeAdmin(admin.ModelAdmin):
    list_display = ("node_id", "name", "device_type", "region", "status", "updated_at")
    search_fields = ("node_id", "name", "region")
    list_filter = ("status", "region")


@admin.register(EnvMonitorRecord)
class EnvMonitorAdmin(admin.ModelAdmin):
    list_display = ("id", "node", "temperature", "humidity", "co2", "recorded_at")
    ordering = ("-recorded_at",)


@admin.register(SoilMonitorRecord)
class SoilMonitorAdmin(admin.ModelAdmin):
    list_display = ("id", "node", "soil_moisture", "soil_ph", "recorded_at")
    ordering = ("-recorded_at",)


@admin.register(AlarmRecord)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "level", "status", "node", "created_at")
    list_filter = ("level", "status")
    ordering = ("-created_at",)


@admin.register(DataAnalysisReport)
class DataAnalysisReportAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "region", "created_at")
    ordering = ("-created_at",)
