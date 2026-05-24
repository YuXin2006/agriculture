from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.models import DeviceNode
from dashboard.serializers import DeviceNodeSerializer
from dashboard.utils import paginate_queryset, read_page_params
from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class DeviceNodeListCreateAPIView(ModelCRUDListCreateAPIView):
    model = DeviceNode
    serializer_class = DeviceNodeSerializer

    def get(self, request):
        page, page_size = read_page_params(request, default_size=self.default_page_size)
        queryset = self.get_queryset()
        items, pagination = paginate_queryset(queryset, page, page_size)
        serializer = self.serializer_class(items, many=True)
        total = pagination["total"]
        online = DeviceNode.objects.filter(status="online").count()
        return Response(
            {
                "results": serializer.data,
                "pagination": pagination,
                "summary": {
                    "total": total,
                    "online": online,
                    "offline": max(total - online, 0),
                },
            }
        )


class DeviceNodeDetailAPIView(ModelCRUDDetailAPIView):
    model = DeviceNode
    serializer_class = DeviceNodeSerializer


class DeviceGPSAPIView(APIView):
    """获取单个节点的 GPS 位置。"""

    def get(self, request, pk):
        node = DeviceNode.objects.filter(pk=pk).first()
        if not node:
            return Response({"detail": "节点不存在"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": node.id,
                "node_id": node.node_id,
                "name": node.name,
                "latitude": node.latitude,
                "longitude": node.longitude,
                "region": node.region,
                "install_location": node.install_location,
            }
        )
