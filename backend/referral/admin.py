from django.contrib import admin
from .models import *


# Register your models here.
@admin.register(PendingReferral)
class PendingReferralAdmin(admin.ModelAdmin):
    list_display = ["referred_user", "referrer", "referral_code", "registered_at"]
    list_filter = ["referrer", "referral_code"]
    # search_fields = ['name']
    # list_editable = ['status']


@admin.register(ReferralNode)
class ReferralNodeAdmin(admin.ModelAdmin):
    list_display = ["user", "parent_node", "root_node", "referral_code"]
    list_filter = ["parent_node", "referral_code"]


@admin.register(PlacementQueue)
class ReferralNodeAdmin(admin.ModelAdmin):
    list_display = ["root_node", "next_available_node", "side", "updated_at"]
    list_filter = ["side", "root_node"]