from rest_framework import viewsets
from map.models import Marker
from map.api.serializers import MarkerSerializer
from rest_framework import generics


class MarkerViewSet(viewsets.ModelViewSet):
    queryset = Marker.objects.all()
    serializer_class = MarkerSerializer
