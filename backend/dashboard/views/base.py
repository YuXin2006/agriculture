from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.utils import paginate_queryset, read_page_params


class ModelCRUDListCreateAPIView(APIView):
    model = None
    serializer_class = None
    default_page_size = 10

    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        page, page_size = read_page_params(request, default_size=self.default_page_size)
        items, pagination = paginate_queryset(self.get_queryset(), page, page_size)
        serializer = self.serializer_class(items, many=True)
        return Response({"results": serializer.data, "pagination": pagination})

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)


class ModelCRUDDetailAPIView(APIView):
    model = None
    serializer_class = None

    def get_object(self, pk):
        return get_object_or_404(self.model, pk=pk)

    def get(self, request, pk):
        instance = self.get_object(pk)
        return Response(self.serializer_class(instance).data)

    def put(self, request, pk):
        instance = self.get_object(pk)
        serializer = self.serializer_class(instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        return Response(self.serializer_class(instance).data)

    def delete(self, request, pk):
        instance = self.get_object(pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
