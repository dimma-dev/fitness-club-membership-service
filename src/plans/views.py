from rest_framework import viewsets, filters, permissions
from .models import MembershipPlan
from .serializers import MembershipPlanSerializer


class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['tier']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
