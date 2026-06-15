from django.urls import include, path
from rest_framework import routers

from membership.views import MembershipViewSet

app_name = "membership"
router = routers.DefaultRouter()
router.register("memberships", MembershipViewSet, basename="membership")

urlpatterns = [
    path("", include(router.urls)),
]
