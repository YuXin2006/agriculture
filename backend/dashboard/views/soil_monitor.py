from dashboard.models import SoilMonitorRecord
from dashboard.serializers import SoilMonitorSerializer
from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class SoilMonitorListCreateAPIView(ModelCRUDListCreateAPIView):
    model = SoilMonitorRecord
    serializer_class = SoilMonitorSerializer


class SoilMonitorDetailAPIView(ModelCRUDDetailAPIView):
    model = SoilMonitorRecord
    serializer_class = SoilMonitorSerializer
