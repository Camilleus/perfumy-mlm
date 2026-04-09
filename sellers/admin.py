from django.contrib import admin
from .models import Seller

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'sponsor', 'commission_rate', 'is_approved', 'created_at']
    list_editable = ['is_approved', 'commission_rate']
    search_fields = ['user__username']
    actions = ['approve_sellers']

    def approve_sellers(self, request, queryset):
        queryset.update(is_approved=True)
    approve_sellers.short_description = 'Zatwierdź wybranych sprzedawców'