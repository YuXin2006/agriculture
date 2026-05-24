from django.db import models


class SensorData(models.Model):
    """历史兼容：总览页聚合传感器读数。"""

    soil_moisture = models.FloatField(verbose_name="土壤湿度")
    temperature = models.FloatField(verbose_name="温度")
    co2 = models.FloatField(verbose_name="CO2浓度")
    light = models.FloatField(verbose_name="光照强度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="采集时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "传感器数据"
        verbose_name_plural = "传感器数据"


class DeviceNode(models.Model):
    STATUS_CHOICES = [
        ("online", "在线"),
        ("offline", "离线"),
    ]

    node_id = models.CharField(max_length=64, unique=True, verbose_name="节点编号")
    name = models.CharField(max_length=128, verbose_name="节点名称")
    device_type = models.CharField(max_length=64, default="多合一传感器", verbose_name="设备类型")
    region = models.CharField(max_length=128, blank=True, default="", verbose_name="所属区域")
    install_location = models.CharField(max_length=255, blank=True, default="", verbose_name="安装位置")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="online", verbose_name="状态")
    signal_strength = models.PositiveSmallIntegerField(default=4, verbose_name="信号强度")
    battery_level = models.PositiveSmallIntegerField(default=100, verbose_name="电量百分比")
    latitude = models.FloatField(null=True, blank=True, verbose_name="纬度")
    longitude = models.FloatField(null=True, blank=True, verbose_name="经度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["node_id"]
        verbose_name = "监测节点"
        verbose_name_plural = "监测节点"

    def __str__(self):
        return self.name or self.node_id


class EnvMonitorRecord(models.Model):
    node = models.ForeignKey(
        DeviceNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="env_records",
        verbose_name="关联节点",
    )
    temperature = models.FloatField(verbose_name="空气温度(℃)")
    humidity = models.FloatField(verbose_name="空气湿度(%)")
    co2 = models.FloatField(verbose_name="CO2(ppm)")
    light = models.FloatField(verbose_name="光照(lux)")
    pressure = models.FloatField(default=101.3, verbose_name="大气压(kPa)")
    air_quality = models.PositiveSmallIntegerField(default=50, verbose_name="空气质量指数")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="采集时间")

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "环境监测记录"
        verbose_name_plural = "环境监测记录"


class SoilMonitorRecord(models.Model):
    node = models.ForeignKey(
        DeviceNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="soil_records",
        verbose_name="关联节点",
    )
    soil_moisture = models.FloatField(verbose_name="土壤湿度(%)")
    soil_ph = models.FloatField(default=6.8, verbose_name="土壤pH")
    soil_temperature = models.FloatField(verbose_name="土壤温度(℃)")
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name="采集时间")

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "土壤监测记录"
        verbose_name_plural = "土壤监测记录"


class AlarmRecord(models.Model):
    LEVEL_CHOICES = [
        ("info", "提示"),
        ("warn", "警告"),
        ("critical", "严重"),
    ]
    STATUS_CHOICES = [
        ("active", "未处理"),
        ("resolved", "已处理"),
    ]

    node = models.ForeignKey(
        DeviceNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alarms",
        verbose_name="关联节点",
    )
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default="warn", verbose_name="级别")
    title = models.CharField(max_length=128, verbose_name="告警标题")
    message = models.TextField(blank=True, default="", verbose_name="告警描述")
    detail = models.CharField(max_length=255, blank=True, default="", verbose_name="详情")
    metric_value = models.FloatField(null=True, blank=True, verbose_name="当前值")
    threshold = models.FloatField(null=True, blank=True, verbose_name="阈值")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", verbose_name="处理状态")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="告警时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "告警记录"
        verbose_name_plural = "告警记录"


class DataAnalysisReport(models.Model):
    """数据分析模块：可保存的分析任务/报告。"""

    title = models.CharField(max_length=128, verbose_name="标题")
    description = models.TextField(blank=True, default="", verbose_name="说明")
    region = models.CharField(max_length=128, blank=True, default="", verbose_name="分析区域")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "数据分析报告"
        verbose_name_plural = "数据分析报告"
