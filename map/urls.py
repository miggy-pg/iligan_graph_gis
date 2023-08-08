from django.contrib import admin
from django.urls import path

from .views import index
from .views import modifymarker_view
from rest_framework import routers
from map.api.views import MarkerViewSet
from django.urls import path, include


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"", MarkerViewSet)

urlpatterns = [
    path("", index, name="index"),
    path("markers", include(router.urls)),
    path("modifymarker/", modifymarker_view, name="modifymarker"),
]
