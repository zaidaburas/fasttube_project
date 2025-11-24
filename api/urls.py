from django.urls import path
from . import views

urlpatterns = [
    path('info', views.info_view),
    path('download', views.download_view),
    path('audio', views.audio_view),
    path('search', views.search_view),
]
