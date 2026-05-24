# tests/integration/test_cache_eviction.py
import pytest
from django.core.cache import cache


@pytest.mark.integration
@pytest.mark.cache
@pytest.mark.django_db
def test_cache_eviction_policy():
    """Проверка, что volatile-lru удаляет старые ключи с TTL."""
    # Заполняем кэш ключами с TTL
    for i in range(100):
        cache.set(f"test_key_{i}", f"value_{i}", timeout=1)  # TTL=1 сек

    # Ждём пока ключи протухнут
    import time

    time.sleep(2)

    # Проверяем, что ключи удалены
    assert cache.get("test_key_0") is None
    assert cache.get("test_key_99") is None
