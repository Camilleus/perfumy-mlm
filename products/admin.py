from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'stock_quantity', 'gender', 'is_available']
    list_filter = ['brand', 'gender', 'is_available']
    search_fields = ['name', 'brand', 'scent_notes']
    list_editable = ['price', 'stock_quantity', 'is_available']