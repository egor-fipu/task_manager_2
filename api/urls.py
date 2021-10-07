from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import UserViewSet, TaskViewSet

router_v1 = SimpleRouter()
router_v1.register(r'auth', UserViewSet, basename='auth')
router_v1.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
]
