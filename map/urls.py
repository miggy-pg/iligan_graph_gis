from django.contrib import admin
from django.urls import path

from .views import index
from .views import modifymarker_view

urlpatterns = [
    path('', index, name="index"),
    path('modifymarker/', modifymarker_view, name="modifymarker"),
]