from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import OrderViewSet, ServiceViewSet, UserProfileViewSet

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"profiles", UserProfileViewSet, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
