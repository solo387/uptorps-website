from django.contrib import admin
from .models import PremiumPackage, UserPremiumSubscription

@admin.register(PremiumPackage)
class PremiumPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'max_referrals', 'status']
    list_filter = ['status', 'duration_days']
    search_fields = ['name']
    list_editable = ['status']

@admin.register(UserPremiumSubscription)
class UserPremiumSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'package']
    list_filter = ['user', 'status']
    search_fields = ['status', 'package']