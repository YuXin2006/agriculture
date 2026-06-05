from django.db import connection
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SensorData


TABLE_CANDIDATES = [
    "dashboard_sensordata",
    "sensor_data",
    "sensor_records",
    "environment_data",
    "dashboard_sensorrecord",
    "dashboard_data",
]

FIELD_CANDIDATES = {
    "soil_moisture": ["soil_moisture", "humidity", "soil_humidity"],
    "temperature": ["temperature", "temp", "soil_temperature"],
    "co2": ["co2", "co2_ppm", "carbon_dioxide"],
    "light": ["light", "light_intensity", "lux"],
    "node_id": ["node_id", "node", "device_id"],
    "region": ["region", "area", "zone"],
    "status": ["status", "state"],
    "timestamp": ["timestamp", "created_at", "updated_at", "time"],
}


def _table_exists(cursor, table_name):
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
        [table_name],
    ).fetchone()
    return row is not None


def _table_columns(cursor, table_name):
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _pick_column(columns, aliases):
    for alias in aliases:
        if alias in columns:
            return alias
    return None


def _resolve_source_table(cursor):
    for table_name in TABLE_CANDIDATES:
        if not _table_exists(cursor, table_name):
            continue
        columns = _table_columns(cursor, table_name)
        mapping = {
            key: _pick_column(columns, aliases)
            for key, aliases in FIELD_CANDIDATES.items()
        }
        if all(mapping[key] for key in ("soil_moisture", "temperature", "co2", "light")):
            return table_name, mapping
    return None, None


def _read_page_params(request, default_size=10):
    try:
        page = int(request.query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", default_size))
    except (TypeError, ValueError):
        page_size = default_size

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    return page, page_size


class OverviewAPIView(APIView):
    def get(self, request):
        page, page_size = _read_page_params(request, default_size=10)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            table_name, mapping = _resolve_source_table(cursor)
            if not table_name:
                return Response(
                    {
                        "metrics": {
                            "soil_moisture": None,
                            "temperature": None,
                            "co2": None,
                            "light": None,
                        },
                        "nodes": [],
                        "node_pagination": {
                            "page": page,
                            "page_size": page_size,
                            "total": 0,
                            "total_pages": 0,
                        },
                        "chart": [],
                        "heatmap": [],
                    }
                )

            avg_sql = (
                f"SELECT AVG({mapping['soil_moisture']}), AVG({mapping['temperature']}), "
                f"AVG({mapping['co2']}), AVG({mapping['light']}) FROM {table_name}"
            )
            avg_row = cursor.execute(avg_sql).fetchone() or (None, None, None, None)

            select_node_id = mapping["node_id"] or "'-'"
            select_region = mapping["region"] or "'-'"
            select_status = mapping["status"] or "'未知'"
            order_column = mapping["timestamp"] or "rowid"
            total_nodes = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            total_pages = (total_nodes + page_size - 1) // page_size if total_nodes else 0

            nodes_sql = (
                f"SELECT {select_node_id}, {select_region}, {mapping['soil_moisture']}, "
                f"{mapping['temperature']}, {mapping['co2']}, {mapping['light']}, {select_status} "
                f"FROM {table_name} ORDER BY {order_column} DESC LIMIT {page_size} OFFSET {offset}"
            )
            node_rows = cursor.execute(nodes_sql).fetchall()

        data = {
            "metrics": {
                "soil_moisture": round(avg_row[0], 2) if avg_row[0] is not None else None,
                "temperature": round(avg_row[1], 2) if avg_row[1] is not None else None,
                "co2": round(avg_row[2], 2) if avg_row[2] is not None else None,
                "light": round(avg_row[3], 2) if avg_row[3] is not None else None,
            },
            "nodes": [
                {
                    "node_id": row[0],
                    "region": row[1],
                    "soil_moisture": row[2],
                    "temperature": row[3],
                    "co2": row[4],
                    "light": row[5],
                    "status": row[6],
                }
                for row in node_rows
            ],
            "node_pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_nodes,
                "total_pages": total_pages,
            },
            "chart": [],
            "heatmap": [],
        }
        return Response(data)


def _serialize_sensor(instance):
    return {
        "id": instance.id,
        "soil_moisture": instance.soil_moisture,
        "temperature": instance.temperature,
        "co2": instance.co2,
        "light": instance.light,
        "created_at": instance.created_at,
    }


def _parse_sensor_payload(data, partial=False):
    fields = ("soil_moisture", "temperature", "co2", "light")
    payload = {}
    for field in fields:
        value = data.get(field, None)
        if value is None:
            if partial:
                continue
            raise ValueError(f"{field} 为必填项")
        try:
            payload[field] = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field} 必须是数字")
    return payload


class SensorDataListCreateAPIView(APIView):
    def get(self, request):
        page, page_size = _read_page_params(request, default_size=10)
        total = SensorData.objects.count()
        total_pages = (total + page_size - 1) // page_size if total else 0
        offset = (page - 1) * page_size
        queryset = SensorData.objects.all()[offset : offset + page_size]
        return Response(
            {
                "results": [_serialize_sensor(item) for item in queryset],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
            }
        )

    def post(self, request):
        try:
            payload = _parse_sensor_payload(request.data, partial=False)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        instance = SensorData.objects.create(**payload)
        return Response(_serialize_sensor(instance), status=status.HTTP_201_CREATED)


class SensorDataDetailAPIView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        return Response(_serialize_sensor(instance))

    def put(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        try:
            payload = _parse_sensor_payload(request.data, partial=False)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        for key, value in payload.items():
            setattr(instance, key, value)
        instance.save()
        return Response(_serialize_sensor(instance))

    def patch(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        try:
            payload = _parse_sensor_payload(request.data, partial=True)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not payload:
            return Response({"detail": "至少提供一个可更新字段"}, status=status.HTTP_400_BAD_REQUEST)
        for key, value in payload.items():
            setattr(instance, key, value)
        instance.save()
        return Response(_serialize_sensor(instance))

    def delete(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
