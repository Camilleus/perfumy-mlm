from django.contrib import admin
from .models import Sale, Commission

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['seller', 'product', 'quantity', 'total_amount', 'sale_date']
    list_filter = ['seller', 'sale_date']

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['seller', 'sale', 'amount', 'level', 'created_at']
    list_filter = ['seller', 'level']