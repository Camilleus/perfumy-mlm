from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'email', 'rating', 'verified_purchase', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['name', 'email', 'product__name']
    readonly_fields = ['created_at', 'verified_purchase']