from django.contrib import admin
from .models import Coupon, CouponUsage, Order, OrderAddress, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'user', 'status', 'payment_method', 'grand_total', 'created_at')
    inlines = [OrderItemInline]

admin.site.register(Coupon)
admin.site.register(CouponUsage)
admin.site.register(OrderAddress)
