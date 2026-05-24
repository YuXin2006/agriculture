from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.models import SensorData
from dashboard.serializers import SensorDataSerializer
from dashboard.services.overview import build_overview_payload
from dashboard.utils import read_page_params


class OverviewAPIView(APIView):
    """总览页聚合数据：一次返回 meta、传感器卡片、告警、图表、设备列表等。"""

    def get(self, request):
        page, page_size = read_page_params(request, default_size=8)
        region = request.query_params.get("region") or None
        data = build_overview_payload(page=page, page_size=page_size, region=region)
        return Response(data)


def _serialize_sensor(instance):
    return SensorDataSerializer(instance).data


class SensorDataListCreateAPIView(APIView):
    def get(self, request):
        page, page_size = read_page_params(request, default_size=10)
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
        serializer = SensorDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(_serialize_sensor(instance), status=status.HTTP_201_CREATED)


class SensorDataDetailAPIView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        return Response(_serialize_sensor(instance))

    def put(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        serializer = SensorDataSerializer(instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(_serialize_sensor(instance))

    def patch(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        serializer = SensorDataSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(_serialize_sensor(instance))

    def delete(self, request, pk):
        instance = get_object_or_404(SensorData, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
