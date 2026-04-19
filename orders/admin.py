from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'phone', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_editable = ['status']
    readonly_fields = ['created_at']
    inlines = [OrderItemInline]