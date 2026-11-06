from django.contrib import admin

from .models import Payment, PaymentTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'method', 'status', 'amount', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('order__order_code', 'order__user__email')


admin.site.register(PaymentTransaction)
