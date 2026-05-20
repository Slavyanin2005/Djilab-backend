# tests/integration/test_orders.py
from decimal import Decimal

import pytest
from rest_framework import status

from catalog.models import Order, OrderItem


@pytest.mark.integration
@pytest.mark.orders
@pytest.mark.django_db
class TestAddToOrder:
    """Integration-тесты добавления в заказ."""

    def test_add_to_order_creates_draft(self, authenticated_client, user, service):
        """Позитивный добавление создаёт черновик заказа."""
        response = authenticated_client.post(f"/api/services/{service.id}/add_to_order/", {"quantity": 2})

        assert response.status_code == status.HTTP_200_OK
        assert Order.objects.filter(creator=user, status="draft").exists()

        order = Order.objects.get(creator=user, status="draft")
        assert OrderItem.objects.filter(order=order, service=service, quantity=2).exists()

    def test_add_to_order_unauthenticated(self, api_client, service):
        """Негативный неавторизованный пользователь."""
        response = api_client.post(f"/api/services/{service.id}/add_to_order/", {"quantity": 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_add_to_order_nonexistent_service(self, authenticated_client):
        """Негативный несуществующая услуга."""
        response = authenticated_client.post("/api/services/99999/add_to_order/", {"quantity": 1})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_order_total_calculation(self, authenticated_client, user, service):
        """Проверка расчёта итоговой суммы."""
        authenticated_client.post(f"/api/services/{service.id}/add_to_order/", {"quantity": 3})

        order = Order.objects.get(creator=user, status="draft")
        expected_total = service.price * Decimal(3)

        assert order.total == expected_total
        assert order.items_count == 1
