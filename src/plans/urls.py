from rest_framework.routers import DefaultRouter
from .views import MembershipPlanViewSet

router = DefaultRouter()
router.register("", MembershipPlanViewSet)

urlpatterns = router.urls
