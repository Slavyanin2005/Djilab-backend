from django.contrib.auth.models import User
from django.db import models


class Service(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="ID")
    name = models.CharField(max_length=200, verbose_name="Наименование")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    status = models.CharField(
        max_length=10, choices=[("active", "Действует"), ("deleted", "Удалён")], default="active", verbose_name="Статус"
    )

    # минио ключи
    image_key = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ключ изображения")
    video_key = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ключ видео")
    image_key_2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Доп. фото 2")
    image_key_3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Доп. фото 3")
    image_key_4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Доп. фото 4")
    image_key_5 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Доп. фото 5")

    category = models.CharField(max_length=50, verbose_name="Категория")
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name="Производитель")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        db_table = "services"
        ordering = ["name"]


class Order(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="ID заявки")

    status = models.CharField(
        max_length=10,
        choices=[
            ("draft", "Черновик"),
            ("deleted", "Удалён"),
            ("formed", "Сформирован"),
            ("completed", "Завершён"),
            ("rejected", "Отклонён"),
        ],
        default="draft",
        verbose_name="Статус",
    )

    # Связь с пользователем
    creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Создатель")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    formed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата формирования")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")

    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_orders",
        verbose_name="Модератор",
    )

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Итого")
    items_count = models.IntegerField(default=0, verbose_name="Количество услуг")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    def __str__(self):
        return f"Заявка #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        db_table = "orders"
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, verbose_name="Заявка")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    position = models.IntegerField(default=0, verbose_name="Позиция")
    is_main = models.BooleanField(default=False, verbose_name="Главная услуга")

    # Новое поле для результатов
    result = models.CharField(max_length=255, blank=True, null=True, verbose_name="Результат")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Подытог", blank=True, editable=False)

    def save(self, *args, **kwargs):
        if self.service and self.quantity:
            qty = int(self.quantity)
            self.subtotal = self.service.price * qty
        super().save(*args, **kwargs)

    class Meta:
        db_table = "order_items"
        unique_together = ["order", "service"]
        ordering = ["position"]


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.PROTECT, verbose_name="Пользователь")

    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    company = models.CharField(max_length=100, blank=True, verbose_name="Компания")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        db_table = "user_profiles"
