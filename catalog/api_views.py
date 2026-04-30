from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .minio_client import generate_unique_filename, upload_to_minio
from .models import Order, OrderItem, Service, UserProfile
from .serializers import OrderSerializer, ServiceSerializer, UserProfileSerializer, UserRegistrationSerializer
from .utils import get_current_user


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(status="active")
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category"]
    ordering_fields = ["price", "name", "created_at"]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        data = {}
        for key, value in request.data.items():
            data[key] = value

        if "image" in request.FILES:
            file = request.FILES["image"]
            service_name = request.data.get("name", "service")
            filename = generate_unique_filename(file.name, service_name)
            uploaded_name = upload_to_minio(file, filename)
            if uploaded_name:
                data["image_key"] = uploaded_name
            else:
                return Response({"error": "Ошибка загрузки изображения"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if "video" in request.FILES:
            file = request.FILES["video"]
            service_name = request.data.get("name", "service")
            filename = generate_unique_filename(file.name, service_name)
            uploaded_name = upload_to_minio(file, filename)
            if uploaded_name:
                data["video_key"] = uploaded_name
            else:
                return Response({"error": "Ошибка загрузки видео"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def add_to_order(self, request, pk=None):
        service = self.get_object()
        quantity = request.data.get("quantity", 1)
        user = get_current_user()

        order = Order.objects.filter(creator=user, status="draft").first()
        if not order:
            max_id = Order.objects.aggregate(Max("id"))["id__max"] or 0
            order = Order.objects.create(id=max_id + 1, status="draft", creator=user)

        order_item, created = OrderItem.objects.get_or_create(
            order=order, service=service, defaults={"quantity": quantity}
        )
        if not created:
            order_item.quantity += quantity
            order_item.save()

        order.items_count = OrderItem.objects.filter(order=order).count()
        order.total = sum(item.subtotal for item in OrderItem.objects.filter(order=order))
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(creator=user).exclude(status="deleted")
        if self.action == "list":
            queryset = queryset.exclude(status="draft")
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(formed_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(formed_at__lte=date_to)
        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        return Response(
            {"error": "Заявка создается автоматически при добавлении услуги"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def cart_icon(self, request):
        user = self.request.user
        if user.is_authenticated:
            draft = Order.objects.filter(creator=user, status="draft").first()
            if draft:
                return Response({"id": draft.id, "items_count": draft.items_count})
        return Response({"id": None, "items_count": 0})

    @action(detail=True, methods=["put"], url_path="update_item")
    def update_item(self, request, pk=None):
        order = self.get_object()
        user = self.request.user

        if order.creator != user or order.status != "draft":
            return Response({"error": "Доступ запрещен или заявка не черновик"}, status=status.HTTP_403_FORBIDDEN)

        service_id = request.data.get("service_id")
        if not service_id:
            return Response({"error": "Требуется поле service_id"}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(OrderItem, order=order, service_id=service_id)

        quantity = request.data.get("quantity")
        if quantity is not None:
            item.quantity = quantity
            item.save()

        self._recalculate(order)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["delete"], url_path=r"items/(?P<service_id>\d+)")
    def delete_item(self, request, pk=None, service_id=None):
        order = self.get_object()
        user = self.request.user

        if order.creator != user or order.status != "draft":
            return Response({"error": "Доступ запрещен или заявка не черновик"}, status=status.HTTP_403_FORBIDDEN)

        OrderItem.objects.filter(order=order, service_id=service_id).delete()
        self._recalculate(order)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="update_item_legacy")
    def update_item_legacy(self, request, pk=None):
        order = self.get_object()
        user = self.request.user

        if order.creator != user or order.status != "draft":
            return Response({"error": "Доступ запрещен или заявка не черновик"}, status=status.HTTP_403_FORBIDDEN)

        item_id = request.data.get("item_id")
        action = request.data.get("action")

        order_item = get_object_or_404(OrderItem, id=item_id, order=order)

        if action == "increase":
            order_item.quantity += 1
        elif action == "decrease":
            if order_item.quantity > 1:
                order_item.quantity -= 1
            else:
                order_item.delete()
                self._recalculate(order)
                return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

        order_item.save()
        self._recalculate(order)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="remove_item")
    def remove_item_legacy(self, request, pk=None):
        order = self.get_object()
        user = self.request.user

        if order.creator != user or order.status != "draft":
            return Response({"error": "Доступ запрещен или заявка не черновик"}, status=status.HTTP_403_FORBIDDEN)

        item_id = request.data.get("item_id")
        OrderItem.objects.filter(id=item_id, order=order).delete()

        self._recalculate(order)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"])
    def form(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if order.creator != user or order.status != "draft":
            return Response({"error": "Только создатель может сформировать черновик"}, status=status.HTTP_403_FORBIDDEN)
        if order.items_count == 0:
            return Response({"error": "Нельзя сформировать пустую заявку"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = "formed"
        order.formed_at = timezone.now()
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["put"])
    def complete(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if not user.is_staff:
            return Response({"error": "Только модератор может завершать заявки"}, status=status.HTTP_403_FORBIDDEN)
        if order.status != "formed":
            return Response(
                {"error": "Можно завершать только сформированные заявки"}, status=status.HTTP_400_BAD_REQUEST
            )
        action_type = request.data.get("action", "complete")
        order.status = "completed" if action_type == "complete" else "rejected"
        order.completed_at = timezone.now()
        order.moderator = user
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def delete(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if order.creator != user:
            return Response({"error": "Доступ запрещен"}, status=status.HTTP_403_FORBIDDEN)
        if order.status != "draft":
            return Response({"error": "Можно удалить только черновик"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = "deleted"
        order.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None, *args, **kwargs):
        order = self.get_object()
        user = self.request.user
        if order.creator != user:
            return Response({"error": "Доступ запрещен"}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, pk, *args, **kwargs)

    def _recalculate(self, order):
        order.items_count = OrderItem.objects.filter(order=order).count()
        order.total = sum(item.subtotal for item in OrderItem.objects.filter(order=order))
        order.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserProfile.objects.filter(user=user)
        return UserProfile.objects.none()

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            auth_login(request, user)
            return Response(
                {"id": user.id, "username": user.username, "message": "Регистрация успешна"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Имя пользователя и пароль обязательны"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return Response(
                {"message": "Вход успешен", "username": user.username, "id": user.id, "is_staff": user.is_staff}
            )

        return Response({"error": "Неверное имя пользователя или пароль"}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        auth_logout(request)
        return Response({"message": "Выход успешен"})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        return Response({"id": user.id, "username": user.username, "email": user.email, "is_staff": user.is_staff})
