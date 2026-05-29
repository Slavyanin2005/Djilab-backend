import hashlib
import logging

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.core.cache import cache
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from prometheus_client import Counter, Gauge
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem, Service, UserProfile
from .serializers import OrderSerializer, ServiceSerializer, UserProfileSerializer, UserRegistrationSerializer

logger = logging.getLogger(__name__)

AUTH_SUCCESS = Counter("auth_login_success_total", "Successful login attempts")
AUTH_FAILURE = Counter("auth_login_failed_total", "Failed login attempts")
AUTH_REGISTER_SUCCESS = Counter("auth_register_success_total", "Successful registrations")
CACHE_HIT = Counter("cache_hits_total", "Cache hit count", ["resource"])
CACHE_MISS = Counter("cache_misses_total", "Cache miss count", ["resource"])
CACHE_MEMORY_USAGE = Gauge("cache_memory_usage_bytes", "Redis memory usage in bytes")

CACHE_TTL = 600


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.filter(status="active")
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category"]
    ordering_fields = ["price", "name", "created_at"]
    permission_classes = [AllowAny]

    def _get_cache_key(self, prefix: str, params: dict = None) -> str:
        param_str = f"{sorted(params.items())}" if params else ""
        key_base = f"{prefix}_{param_str}"
        return f"djilab_services_{hashlib.md5(key_base.encode()).hexdigest()[:12]}"

    def list(self, request, *args, **kwargs):
        cache_key = self._get_cache_key("list", dict(request.query_params))
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"CACHE HIT: key={cache_key}")
            response = Response(cached_data)
            response.headers["X-Cache-Status"] = "HIT"
            return response

        logger.info(f"CACHE MISS: key={cache_key}. Fetching from DB.")
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        cache.set(cache_key, data, timeout=CACHE_TTL)
        logger.info(f"CACHE SET: key={cache_key}, TTL={CACHE_TTL}s")
        response = Response(data)
        response.headers["X-Cache-Status"] = "MISS"
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._invalidate_services_cache()
        logger.info("CACHE INVALIDATED: services cache after CREATE")
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self._invalidate_services_cache()
        logger.info("CACHE INVALIDATED: services cache after UPDATE")
        return response

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        self._invalidate_services_cache()
        logger.info("CACHE INVALIDATED: services cache after DELETE")
        return response

    def _invalidate_services_cache(self):
        try:
            from django_redis import get_redis_connection

            redis_conn = get_redis_connection("default")
            pattern = "djilab*djilab_services_*"
            for key in redis_conn.scan_iter(match=pattern):
                redis_conn.delete(key)
                logger.debug(f"Deleted cache key: {key.decode()}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")

    @action(detail=True, methods=["post"])
    def add_to_order(self, request, pk=None):
        service = self.get_object()
        quantity = request.data.get("quantity", 1)
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Требуется авторизация"}, status=status.HTTP_401_UNAUTHORIZED)
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

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        service = self.get_object()
        limit = int(request.query_params.get("limit", 4))
        current_text = f"{service.name} {service.description} {service.category}".lower()
        current_words = set(current_text.split())
        all_services = Service.objects.filter(status="active").exclude(id=service.id)
        similarities = []
        for s in all_services:
            service_text = f"{s.name} {s.description} {s.category}".lower()
            service_words = set(service_text.split())
            intersection = len(current_words.intersection(service_words))
            union = len(current_words.union(service_words))
            similarity = intersection / union if union > 0 else 0
            similarities.append((s, similarity))
        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_services = [s for s, _ in similarities[:limit]]
        serializer = self.get_serializer(similar_services, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = Service.objects.filter(status="active")
        min_price = self.request.query_params.get("min_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        max_price = self.request.query_params.get("max_price")
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.filter(creator=user).exclude(status="deleted")
        if user.is_staff:
            queryset = Order.objects.exclude(status="deleted")
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
            {"error": "Заявка создается автоматически при добавлении услуги"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
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
            return Response(
                {"error": "Доступ запрещен или заявка не черновик"},
                status=status.HTTP_403_FORBIDDEN,
            )
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
            return Response(
                {"error": "Доступ запрещен или заявка не черновик"},
                status=status.HTTP_403_FORBIDDEN,
            )
        OrderItem.objects.filter(order=order, service_id=service_id).delete()
        self._recalculate(order)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="update_item_legacy")
    def update_item_legacy(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if order.creator != user or order.status != "draft":
            return Response(
                {"error": "Доступ запрещен или заявка не черновик"},
                status=status.HTTP_403_FORBIDDEN,
            )
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
            return Response(
                {"error": "Доступ запрещен или заявка не черновик"},
                status=status.HTTP_403_FORBIDDEN,
            )
        item_id = request.data.get("item_id")
        OrderItem.objects.filter(id=item_id, order=order).delete()
        self._recalculate(order)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["put"])
    def form(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if order.creator != user or order.status != "draft":
            return Response(
                {"error": "Только создатель может сформировать черновик"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if order.items_count == 0:
            return Response(
                {"error": "Нельзя сформировать пустую заявку"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "formed"
        order.formed_at = timezone.now()
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["put"])
    def complete(self, request, pk=None):
        order = self.get_object()
        user = self.request.user
        if not user.is_staff:
            return Response(
                {"error": "Только модератор может завершать заявки"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if order.status != "formed":
            return Response(
                {"error": "Можно завершать только сформированные заявки"},
                status=status.HTTP_400_BAD_REQUEST,
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
        if order.creator != user and not user.is_staff:
            return Response({"error": "Доступ запрещен"}, status=status.HTTP_403_FORBIDDEN)
        if "comment" in request.data and request.data["comment"]:
            new_comment = request.data["comment"].strip()
            if new_comment:
                timestamp = timezone.now().strftime("%d.%m.%Y %H:%M")
                author = "Модератор" if user.is_staff else user.username
                comment_entry = f"[{timestamp}] {author}: {new_comment}\n"
                existing = order.comment or ""
                order.comment = existing + comment_entry
                order.save(update_fields=["comment"])
                return Response(OrderSerializer(order).data)
        if "status" in request.data and user.is_staff:
            new_status = request.data["status"]
            valid_statuses = ["draft", "formed", "completed", "rejected", "deleted"]
            if new_status in valid_statuses:
                if order.status == "completed" and new_status == "formed":
                    order.status = new_status
                    order.completed_at = None
                    order.moderator = None
                    order.save(update_fields=["status", "completed_at", "moderator"])
                    return Response(OrderSerializer(order).data)
                order.status = new_status
                if new_status in ["completed", "rejected"]:
                    order.completed_at = timezone.now()
                    order.moderator = user
                order.save(update_fields=["status", "completed_at", "moderator"])
                return Response(OrderSerializer(order).data)
        return super().partial_update(request, pk, *args, **kwargs)

    def _recalculate(self, order):
        order.items_count = OrderItem.objects.filter(order=order).count()
        order.total = sum(item.subtotal for item in OrderItem.objects.filter(order=order))
        order.save()


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = None  # Отключаем поиск по pk

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserProfile.objects.filter(user=user)
        return UserProfile.objects.none()

    def get_object(self):
        # Всегда возвращаем профиль текущего пользователя
        return self.get_queryset().first()

    def retrieve(self, request, *args, **kwargs):
        # GET /api/profiles/me/
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # PUT /api/profiles/me/
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        # PATCH /api/profiles/me/
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Successful registration for user: {user.username}")
            AUTH_REGISTER_SUCCESS.inc()
            return Response(
                {"id": user.id, "username": user.username, "message": "Регистрация успешна"},
                status=status.HTTP_201_CREATED,
            )
        logger.warning(f"Failed registration attempt: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            logger.warning(f"Failed login attempt (missing credentials): {username}")
            AUTH_FAILURE.inc()
            return Response(
                {"error": "Имя пользователя и пароль обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session.save()
            from django.middleware.csrf import get_token

            csrf_token = get_token(request)
            logger.info(f"Successful login for user: {username}")
            AUTH_SUCCESS.inc()
            return Response(
                {
                    "message": "Вход успешен",
                    "username": user.username,
                    "id": user.id,
                    "is_staff": user.is_staff,
                    "csrfToken": csrf_token,
                }
            )
        logger.warning(f"Failed login attempt for user: {username}")
        AUTH_FAILURE.inc()
        return Response(
            {"error": "Неверное имя пользователя или пароль"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        logger.info(f"Logout for user: {request.user.username}")
        auth_logout(request)
        request.session.flush()
        return Response({"message": "Выход успешен"})

    @action(detail=False, methods=["put"], url_path="me/change_password", permission_classes=[IsAuthenticated])
    def change_password_action(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        if not user.check_password(current_password):
            return Response({"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response(
                {"error": "Пароль должен содержать не менее 8 символов"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response({"message": "Пароль успешно изменён"})
