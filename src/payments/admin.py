from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в таблице со списком платежей
    list_display = (
        "id",
        "membership",
        "status",
        "type",
        "money_to_pay",
        "created_at"
    )

    # Боковая панель с фильтрами (очень удобно для бухгалтерии)
    list_filter = ("status", "type", "created_at")

    # Поля, по которым будет работать строка поиска
    # "membership__id" позволит искать платежи по ID конкретного абонемента
    search_fields = ("session_id", "membership__id")

    # Делаем эти поля доступными только для чтения внутри админки.
    # Администратор не должен вручную менять ID сессии Stripe или сумму.
    readonly_fields = ("session_id", "session_url", "created_at")

    # Настройка группировки полей при детальном просмотре платежа
    fieldsets = (
        ("General Information", {
            "fields": ("membership", "status", "type", "money_to_pay")
        }),
        ("Stripe Technical Data", {
            "fields": ("session_id", "session_url"),
            "description": "Technical session data synchronized with Stripe API."
        }),
        ("Timestamps", {
            "fields": ("created_at",),
        }),
    )

    # Запрещаем администраторам вручную создавать платежи через кнопку "Add",
    # так как они должны создаваться строго через Stripe API.
    def has_add_permission(self, request):
        return False