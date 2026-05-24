from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.services import run_ai_analysis


class AIAnalysisAPIView(APIView):
    def post(self, request):
        if not request.data:
            return Response(
                {"detail": "请传入传感器数据，如 soil_moisture、temperature、co2、light"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = run_ai_analysis(request.data)
        return Response(result)
