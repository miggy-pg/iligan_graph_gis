from import_export import resources
from .models import Marker


class MarkerResource(resources.ModelResource):
    class Meta:
        model = Marker