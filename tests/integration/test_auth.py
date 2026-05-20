# tests/integration/test_auth.py
import pytest
from django.contrib.auth.models import User
from rest_framework import status


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.django_db
class TestUserRegistration:
    """Integration-тесты регистрации."""

    def test_registration_success(self, api_client):
        """Позитивный сценарий успешная регистрация."""
        data = {"username": "newuser", "email": "new@example.com", "password": "NewPass123!"}
        response = api_client.post("/api/profiles/register/", data)

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()
        assert "id" in response.data

    def test_registration_duplicate_username(self, api_client, user):
        """Негативный регистрация с существующим username."""
        data = {"username": user.username, "email": "other@example.com", "password": "OtherPass123!"}
        response = api_client.post("/api/profiles/register/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_registration_weak_password(self, api_client):
        """Негативный: слабый пароль."""
        data = {"username": "weakpass", "email": "weak@example.com", "password": "123"}
        response = api_client.post("/api/profiles/register/", data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.django_db
class TestUserLogin:
    """Integration-тесты авторизации."""

    def test_login_success(self, api_client, user):
        """Позитивный успешный вход."""
        data = {"username": "testuser", "password": "TestPass123!"}
        response = api_client.post("/api/profiles/login/", data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "testuser"

    def test_login_wrong_password(self, api_client, user):
        """Негативный неверный пароль."""
        data = {"username": "testuser", "password": "WrongPass!"}
        response = api_client.post("/api/profiles/login/", data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
