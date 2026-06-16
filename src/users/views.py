from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.serializers import UserSerializer


@extend_schema(
    tags=["Users"],
    summary="Register a new member",
    description="Creates a new member profile in the system.",
    responses={
        201: OpenApiResponse(response=UserSerializer, description="Member successfully created."),
        400: OpenApiResponse(description="Validation error (e.g., email already exists or invalid data).")
    }
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


@extend_schema(
    tags=["Users"],
    summary="Manage member profile",
    description="Allows the currently authenticated member to retrieve or update their own profile information.",
    responses={
        200: OpenApiResponse(response=UserSerializer, description="Profile data retrieved or updated successfully."),
        401: OpenApiResponse(description="Authentication credentials were not provided or are invalid.")
    }
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
