from rest_framework import serializers

from .models import AlarmRecord, DataAnalysisReport, DeviceNode, EnvMonitorRecord, SensorData, SoilMonitorRecord


class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ("id", "soil_moisture", "temperature", "co2", "light", "created_at")
        read_only_fields = ("id", "created_at")


class DeviceNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceNode
        fields = (
            "id",
            "node_id",
            "name",
            "device_type",
            "region",
            "install_location",
            "status",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class EnvMonitorSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source="node.node_id", read_only=True, allow_null=True)

    class Meta:
        model = EnvMonitorRecord
        fields = (
            "id",
            "node",
            "node_id",
            "temperature",
            "humidity",
            "co2",
            "light",
            "pressure",
            "air_quality",
            "recorded_at",
        )
        read_only_fields = ("id", "recorded_at")


class SoilMonitorSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source="node.node_id", read_only=True, allow_null=True)

    class Meta:
        model = SoilMonitorRecord
        fields = (
            "id",
            "node",
            "node_id",
            "soil_moisture",
            "soil_ph",
            "soil_temperature",
            "recorded_at",
        )
        read_only_fields = ("id", "recorded_at")


class AlarmSerializer(serializers.ModelSerializer):
    node_id = serializers.CharField(source="node.node_id", read_only=True, allow_null=True)

    class Meta:
        model = AlarmRecord
        fields = (
            "id",
            "node",
            "node_id",
            "level",
            "title",
            "message",
            "detail",
            "metric_value",
            "threshold",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DataAnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataAnalysisReport
        fields = ("id", "title", "description", "region", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
