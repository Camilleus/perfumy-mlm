from django.contrib import admin
from .models import Seller

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'sponsor', 'commission_rate', 'created_at']
    search_fields = ['user__username']