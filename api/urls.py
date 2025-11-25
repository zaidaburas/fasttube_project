from django.urls import path,include
from . import views

urlpatterns = [
    path("api/info", views.info_view),
    # path("api/download", views.download_view),
]