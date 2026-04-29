from django.contrib.auth.models import User
from django.db.models import Max


def get_current_user():
    # Получаем или создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username="test_user", defaults={"email": "test@example.com", "first_name": "Test", "last_name": "User"}
    )
    return user


def get_next_id(model_class):
    max_id = model_class.objects.aggregate(Max("id"))["id__max"]
    return (max_id or 0) + 1
