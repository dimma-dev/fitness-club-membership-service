from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import CreateUserView, ManageUserView

decorated_token_obtain = extend_schema(tags=["Users"])(TokenObtainPairView)
decorated_token_refresh = extend_schema(tags=["Users"])(TokenRefreshView)

urlpatterns = [
    path("", CreateUserView.as_view(), name="register"),
    path("token/", decorated_token_obtain.as_view(), name="token_obtain_pair"),
    path("token/refresh/", decorated_token_refresh.as_view(), name="token_refresh"),
    path("me/", ManageUserView.as_view(), name="manage-user"),
]

app_name = "users"
