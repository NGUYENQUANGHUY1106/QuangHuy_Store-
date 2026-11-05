from django.db import models
from django.core.validators import MaxValueValidator

from Login.models import User
from Product.models import ProductVariant


class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True)
    discount_percent = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    min_order = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'coupon'
        constraints = [models.CheckConstraint(condition=models.Q(discount_percent__lte=100), name='coupon_percent_max_100')]


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'), ('confirmed', 'Đã xác nhận'),
        ('shipping', 'Đang giao'), ('completed', 'Hoàn tất'), ('cancelled', 'Đã hủy'),
    ]
    PAYMENT_CHOICES = [('cod', 'Thanh toán khi nhận hàng')]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    order_code = models.CharField(max_length=20, unique=True)
    idempotency_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    shipping_method = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=14, decimal_places=0)
    discount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    shipping_fee = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=0)
    coupon_code = models.CharField(max_length=30, blank=True)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order'
        ordering = ['-created_at']


class OrderAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping_address')
    recipient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=10)
    province = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    detail = models.CharField(max_length=255)

    class Meta:
        db_table = 'order_address'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=80)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=14, decimal_places=0)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=14, decimal_places=0)

    class Meta:
        db_table = 'order_item'


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usage'
        constraints = [models.UniqueConstraint(fields=['coupon', 'user'], name='one_coupon_use_per_user')]


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_history'
        ordering = ['created_at', 'id']
