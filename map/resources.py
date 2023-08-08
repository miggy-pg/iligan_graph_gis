from import_export import resources
from map.models import Marker


class MarkerResource(resources.ModelResource):
    class Meta:
        model = Marker
