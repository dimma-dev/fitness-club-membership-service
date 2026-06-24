from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import MembershipPlan
from .serializers import MembershipPlanSerializer


@extend_schema(tags=["Membership Plans"])
class MembershipPlanViewSet(viewsets.ModelViewSet):
    queryset = MembershipPlan.objects.all()
    serializer_class = MembershipPlanSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tier"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    @extend_schema(
        summary="List all membership plans",
        description="Retrieves a paginated list of fitness club membership plans. Can be filtered by tier."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a specific membership plan",
        description="Get detailed information about a membership plan by its unique ID."
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new membership plan",
        description="Creates a new plan with a unique code. Accessible only by system administrators.",
        responses={
            201: OpenApiResponse(response=MembershipPlanSerializer, description="Plan successfully created."),
            400: OpenApiResponse(description="Validation error or duplicate code.")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a membership plan",
        description="Permanently removes a membership plan from the system. Admin only.",
        responses={
            204: OpenApiResponse(description="Plan successfully deleted.")
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
