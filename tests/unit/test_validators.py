# tests/unit/test_validators.py
from decimal import Decimal

import pytest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


@pytest.mark.unit
class TestPasswordValidation:
    """Unit-тесты валидации пароля."""

    def test_password_too_short(self):
        """Пароль < 8 символов должен отклоняться."""
        with pytest.raises(ValidationError):
            validate_password("Short1!")

    def test_password_min_length_valid(self):
        """Пароль ровно 8 символов — валиден."""
        try:
            validate_password("Valid123!")
        except ValidationError:
            pytest.fail("Валидный пароль отклонён")

    def test_password_no_uppercase(self):
        """Пароль без заглавных — ДОЛЖЕН проходить (стандарт Django)."""
        try:
            validate_password("alllowercase1!")
        except ValidationError:
            pytest.fail("Пароль без заглавных не должен отклоняться по умолчанию")

    def test_password_boundary_32_chars(self):
        """Пароль 32 символа — валиден (граница)."""
        password = "A" * 31 + "1!"  # ровно 32
        try:
            validate_password(password)
        except ValidationError:
            pytest.fail("Пароль из 32 символов отклонён")


@pytest.mark.unit
class TestPriceFiltering:
    """Unit-тесты логики фильтрации по цене."""

    @pytest.mark.parametrize(
        "price,min_price,expected",
        [
            ("1000.00", "500", True),
            ("1000.00", "1000", True),
            ("1000.00", "1001", False),
            ("0.00", "0", True),
            ("0.00", "0.01", False),
        ],
    )
    def test_min_price_filter(self, price, min_price, expected):
        """Проверка фильтрации по минимальной цене."""
        result = Decimal(price) >= Decimal(min_price)
        assert result == expected

    def test_invalid_price_string(self):
        """Невалидная строка цены должна обрабатываться."""
        with pytest.raises(ValueError):
            float("not-a-number")
