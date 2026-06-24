from django.contrib import admin
from .models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "plan",
        "status",
        "start_date",
        "end_date",
        "auto_renew"
    )

    list_filter = ("status", "auto_renew", "plan", "start_date")
    search_fields = ("member__email", "=id")
    raw_id_fields = ("member",)
    date_hierarchy = "start_date"
