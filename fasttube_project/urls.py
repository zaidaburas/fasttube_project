from django.urls import path, include
from django.http import JsonResponse

def health(request):
    return JsonResponse({'status': 'OK', 'timestamp': __import__('datetime').datetime.utcnow().isoformat()})

urlpatterns = [
    path('api/', include('api.urls')),
    path('health', health),
]
