from django.contrib import admin

from .models import Marker


class MarkerAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(Marker, MarkerAdmin)