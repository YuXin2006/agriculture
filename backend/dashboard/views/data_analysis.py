from rest_framework import status
from rest_framework.response import Response

from dashboard.models import DataAnalysisReport
from dashboard.serializers import DataAnalysisReportSerializer
from dashboard.services import build_analysis_payload
from dashboard.utils import paginate_queryset, read_page_params
from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class DataAnalysisListCreateAPIView(ModelCRUDListCreateAPIView):
    model = DataAnalysisReport
    serializer_class = DataAnalysisReportSerializer

    def get(self, request):
        page, page_size = read_page_params(request, default_size=self.default_page_size)
        items, pagination = paginate_queryset(self.get_queryset(), page, page_size)
        serializer = self.serializer_class(items, many=True)
        region = request.query_params.get("region")
        dashboard = build_analysis_payload(region=region or None)
        return Response(
            {
                "results": serializer.data,
                "pagination": pagination,
                "chart_24h": dashboard["chart_24h"],
                "heatmap": dashboard["heatmap"],
                "gps_points": dashboard["gps_points"],
            }
        )


class DataAnalysisDetailAPIView(ModelCRUDDetailAPIView):
    model = DataAnalysisReport
    serializer_class = DataAnalysisReportSerializer

    def get(self, request, pk):
        instance = self.get_object(pk)
        dashboard = build_analysis_payload(region=instance.region or None)
        data = self.serializer_class(instance).data
        data.update(
            {
                "chart_24h": dashboard["chart_24h"],
                "heatmap": dashboard["heatmap"],
                "gps_points": dashboard["gps_points"],
            }
        )
        return Response(data)
