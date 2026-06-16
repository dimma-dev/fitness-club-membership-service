from django.contrib import admin
from .models import MembershipPlan


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "duration_days",
        "price",
        "tier",
    )
    list_filter = ("tier", "duration_days")
    search_fields = ("name", "code")
    ordering = ["price"]
    prepopulated_fields = {"code": ("name",)}

    fieldsets = (
        ("General Info", {"fields": ("name", "code", "tier")}),
        ("Pricing & Terms", {"fields": ("duration_days", "price")}),
    )
