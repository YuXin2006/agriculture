from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import (
    AlarmRecord,
    DataAnalysisReport,
    DeviceNode,
    EnvMonitorRecord,
    SensorData,
    SoilMonitorRecord,
)


class Command(BaseCommand):
    help = "写入演示用节点、监测与告警数据"

    def handle(self, *args, **options):
        if DeviceNode.objects.exists():
            self.stdout.write(self.style.WARNING("已有数据，跳过 seed"))
            return

        nodes = []
        coords = [
            (31.2304, 121.4737),
            (31.2310, 121.4745),
            (31.2298, 121.4728),
            (31.2320, 121.4750),
        ]
        for i, (lat, lng) in enumerate(coords, start=1):
            node = DeviceNode.objects.create(
                node_id=f"GH-A-{i:02d}",
                name=f"温室A-{i:02d}",
                device_type="多合一传感器" if i % 2 else "土壤探头",
                region="温室 A 区",
                install_location=f"A区第{i}垄",
                status="online" if i < 4 else "offline",
                signal_strength=3 + (i % 2),
                battery_level=90 - i * 5,
                latitude=lat,
                longitude=lng,
            )
            nodes.append(node)

        for node in nodes:
            EnvMonitorRecord.objects.create(
                node=node,
                temperature=24.5 + nodes.index(node) * 0.3,
                humidity=65.0,
                co2=420.0,
                light=8500.0,
                pressure=101.3,
                air_quality=42,
            )
            SoilMonitorRecord.objects.create(
                node=node,
                soil_moisture=52.0 - nodes.index(node) * 2,
                soil_ph=6.8,
                soil_temperature=22.0,
            )

        SensorData.objects.create(
            soil_moisture=48.5,
            temperature=25.2,
            co2=435.0,
            light=9200.0,
        )

        AlarmRecord.objects.create(
            node=nodes[0],
            level="warn",
            title="土壤湿度过低",
            message="当前土壤湿度低于设定阈值",
            detail="当前 41% · 阈值 45%",
            metric_value=41.0,
            threshold=45.0,
            status="active",
        )

        DataAnalysisReport.objects.create(
            title="温室A区日度分析",
            description="24小时环境/土壤趋势",
            region="温室 A 区",
        )

        self.stdout.write(self.style.SUCCESS(f"已创建 {len(nodes)} 个节点及关联演示数据"))
