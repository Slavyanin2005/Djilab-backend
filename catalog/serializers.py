from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import Order, OrderItem, Service, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ["id", "user", "phone", "company", "position", "created_at"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    # ✅ Валидатор: только латиница, цифры, подчёркивание
    username = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9_]+$",
                message="Имя пользователя может содержать только латинские буквы, цифры и подчёркивание.",
            )
        ],
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "first_name", "last_name"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_username(self, value):
        # ✅ Приводим к нижнему регистру
        return value.lower()

    def validate_email(self, value):
        # ✅ Проверяем уникальность email
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value.lower()

    def create(self, validated_data):
        # ✅ Создаём пользователя с хешированным паролем
        user = User.objects.create_user(
            username=validated_data["username"].lower(),
            email=validated_data["email"].lower(),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        # ✅ Создаём профиль автоматически
        UserProfile.objects.create(user=user)
        return user


class ServiceSerializer(serializers.ModelSerializer):
    # Поля для загрузки файлов (write_only=True, чтобы не передавать их в ответе GET)
    image = serializers.FileField(write_only=True, required=False)
    video = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "price",
            "status",
            "image_key",
            "video_key",
            "image_key_2",
            "image_key_3",
            "image_key_4",
            "image_key_5",
            "category",
            "manufacturer",
            "created_at",
            "updated_at",
            "image",
            "video",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        validated_data.pop("image", None)
        validated_data.pop("video", None)
        return Service.objects.create(**validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    service_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "order", "service", "service_id", "quantity", "position", "is_main", "subtotal"]
        read_only_fields = ["order", "subtotal", "service_id"]


class OrderSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    items = OrderItemSerializer(source="orderitem_set", many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "status_display",
            "creator",
            "created_at",
            "formed_at",
            "completed_at",
            "moderator",
            "total",
            "items_count",
            "comment",
            "items",
        ]
        read_only_fields = [
            "creator",
            "status",
            "formed_at",
            "completed_at",
            "moderator",
            "total",
            "items_count",
            "created_at",
        ]
