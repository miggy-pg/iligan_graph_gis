from map.models import Marker
from rest_framework import serializers


class MarkerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Marker
        fields = "__all__"
