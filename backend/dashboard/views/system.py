from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.services.system_status import build_system_status_payload


class SystemStatusAPIView(APIView):
    """运维管理：系统运行状态与数据采集概况（只读）。"""

    def get(self, request):
        return Response(build_system_status_payload())
