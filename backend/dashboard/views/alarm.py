from dashboard.models import AlarmRecord
from dashboard.serializers import AlarmSerializer
from dashboard.views.base import ModelCRUDDetailAPIView, ModelCRUDListCreateAPIView


class AlarmListCreateAPIView(ModelCRUDListCreateAPIView):
    model = AlarmRecord
    serializer_class = AlarmSerializer


class AlarmDetailAPIView(ModelCRUDDetailAPIView):
    model = AlarmRecord
    serializer_class = AlarmSerializer
