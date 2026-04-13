from django.contrib import admin
from .models import Seller, Referral

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['user', 'referral_code', 'credit', 'created_at']
    search_fields = ['user__username', 'referral_code']
    readonly_fields = ['referral_code', 'created_at']

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_email', 'discount_used', 'credit_awarded', 'created_at']
    list_filter = ['discount_used', 'credit_awarded']
