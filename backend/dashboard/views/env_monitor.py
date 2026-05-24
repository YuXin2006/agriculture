from dashboard.models import EnvMonitorRecord
from dashboard.serializers import EnvMonitorSerializer
from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class EnvMonitorListCreateAPIView(ModelCRUDListCreateAPIView):
    model = EnvMonitorRecord
    serializer_class = EnvMonitorSerializer


class EnvMonitorDetailAPIView(ModelCRUDDetailAPIView):
    model = EnvMonitorRecord
    serializer_class = EnvMonitorSerializer
