from django.contrib import admin

from .models import Order, OrderItem, Service, UserProfile  # ✅ Здесь — ПРАВИЛЬНО!


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "price", "category", "status"]
    search_fields = ["name"]
    list_filter = ["status", "category"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "creator", "total", "items_count", "created_at"]
    search_fields = ["id", "creator__username"]
    list_filter = ["status", "created_at"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "service", "quantity", "subtotal"]
    list_filter = ["order", "service"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "phone", "company", "created_at"]
    search_fields = ["user__username", "phone"]
