from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class UserApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_register_user(self) -> None:
        url = reverse("users:register")  # Змінено на register
        payload = {
            "email": "new@test.com",
            "password": "testpassword",
            "first_name": "New",
            "last_name": "User",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@test.com").exists())

    def test_get_token(self) -> None:
        url = reverse("users:token_obtain_pair")
        payload = {"email": "test@test.com", "password": "testpassword"}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_get_profile_unauthorized(self) -> None:
        url = reverse("users:manage-user")  # Змінено на manage-user
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authorized(self) -> None:
        url = reverse("users:manage-user")  # Змінено на manage-user
        self.client.force_authenticate(self.user)

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_update_profile_fields(self) -> None:
        url = reverse("users:manage-user")
        self.client.force_authenticate(self.user)
        payload = {"first_name": "UpdatedName", "last_name": "UpdatedLastName"}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, payload["first_name"])
        self.assertEqual(self.user.last_name, payload["last_name"])

    def test_update_password_hashes_properly(self) -> None:
        url = reverse("users:manage-user")
        self.client.force_authenticate(self.user)
        payload = {"password": "newsecurepassword"}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newsecurepassword"))
