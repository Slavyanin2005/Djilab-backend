# tests/conftest.py
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Service


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="TestPass123!", email="test@example.com")


@pytest.fixture
def authenticated_client(api_client, user):
    """Авторизованный клиент."""
    api_client.force_login(user)
    return api_client


@pytest.fixture
def service(db):
    """Тестовая услуга."""
    return Service.objects.create(
        id=999,
        name="Тестовая услуга",
        description="<li>Тест</li>",
        price=Decimal("1000.00"),
        category="Тест",
        manufacturer="TestCo",
    )
