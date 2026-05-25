from rest_framework import status
from rest_framework.response import Response

# from dashboard.models import DataAnalysisReport
# from dashboard.serializers import DataAnalysisReportSerializer
# from dashboard.services import build_analysis_payload
# from dashboard.utils import paginate_queryset, read_page_params
# from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class DataAnalysisListCreateAPIView:
    """[已注释重构] 数据分析列表视图"""
    default_page_size = 10

    def get(self, request):
        return Response(
            {
                "results": [],
                "pagination": {"page": 1, "page_size": 10, "total": 0, "total_pages": 0},
                "chart_24h": {"labels": [], "temperature": [], "humidity": [], "soil_moisture": []},
                "heatmap": {"grid_size": 5, "points": []},
                "gps_points": [],
            }
        )


class DataAnalysisDetailAPIView:
    """[已注释重构] 数据分析详情视图"""

    def get(self, request, pk):
        return Response({"detail": "数据分析功能正在重构中"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)