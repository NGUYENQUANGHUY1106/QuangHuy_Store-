from django.conf import settings
from django.db import models

from Product.models import ProductVariant


class Warehouse(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    address = models.CharField(max_length=255, blank=True)
    is_online = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    class Meta: db_table = 'warehouse'
    def __str__(self): return f'{self.code} - {self.name}'


class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stocks')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='warehouse_stocks')
    on_hand = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'inventory_stock'
        constraints = [
            models.UniqueConstraint(fields=['warehouse','variant'], name='unique_warehouse_variant_stock'),
            models.CheckConstraint(condition=models.Q(on_hand__gte=models.F('reserved')), name='stock_reserved_not_over_on_hand'),
        ]
    @property
    def available(self): return self.on_hand - self.reserved


class StockMovement(models.Model):
    TYPE_CHOICES = [('adjustment','Điều chỉnh'),('receipt','Nhập kho'),('sale','Xuất bán'),('return','Hoàn kho')]
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    before_quantity = models.PositiveIntegerField()
    after_quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: db_table = 'stock_movement'; ordering = ['-created_at','-id']


class StockCount(models.Model):
    STATUS_CHOICES = [('draft','Bản nháp'),('completed','Hoàn tất')]
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stock_counts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    class Meta: db_table = 'stock_count'; ordering = ['-created_at']


class StockCountItem(models.Model):
    stock_count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='items')
    stock = models.ForeignKey(Stock, on_delete=models.PROTECT)
    system_quantity = models.PositiveIntegerField()
    counted_quantity = models.PositiveIntegerField()
    class Meta:
        db_table = 'stock_count_item'
        constraints = [models.UniqueConstraint(fields=['stock_count','stock'], name='unique_stock_count_item')]
    @property
    def difference(self): return self.counted_quantity - self.system_quantity
