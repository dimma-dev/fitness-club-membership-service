from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from .models import MembershipPlan
from .serializers import MembershipPlanSerializer


class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tier"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
