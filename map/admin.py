from django.contrib import admin
from map.models import Marker


class MarkerAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "category_level"]
    search_fields = ["name"]


admin.site.register(Marker, MarkerAdmin)
