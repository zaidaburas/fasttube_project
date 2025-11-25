from django.urls import path
from .views import get_info, download

urlpatterns = [
    path("api/info", get_info),
    path("api/download", download),
]
