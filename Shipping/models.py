from django.db import models
from Checkout.models import Order

class ShippingMethod(models.Model):
    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    base_fee = models.DecimalField(max_digits=12, decimal_places=0)
    free_from = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    eta_min_days = models.PositiveIntegerField(default=2)
    eta_max_days = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    class Meta: db_table = 'shipping_method'

class ShippingZone(models.Model):
    method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE, related_name='zones')
    province = models.CharField(max_length=100)
    surcharge = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    class Meta:
        db_table = 'shipping_zone'
        constraints = [models.UniqueConstraint(fields=['method', 'province'], name='unique_shipping_method_province')]

class Shipment(models.Model):
    STATUS_CHOICES = [('preparing','Đang chuẩn bị'),('picked','Đã lấy hàng'),('shipping','Đang giao'),('delivered','Đã giao'),('failed','Giao thất bại')]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=100)
    tracking_code = models.CharField(max_length=100, unique=True)
    tracking_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='preparing')
    estimated_delivery = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'shipment'

class ShipmentEvent(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    event_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    description = models.CharField(max_length=255)
    occurred_at = models.DateTimeField()
    class Meta:
        db_table = 'shipment_event'
        ordering = ['occurred_at', 'id']
