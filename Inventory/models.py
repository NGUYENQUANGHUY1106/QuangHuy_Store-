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


class Supplier(models.Model):
    name=models.CharField(max_length=200); code=models.CharField(max_length=30,unique=True)
    phone=models.CharField(max_length=20,blank=True); email=models.EmailField(blank=True); address=models.CharField(max_length=255,blank=True); is_active=models.BooleanField(default=True)
    class Meta: db_table='supplier'
    def __str__(self): return f'{self.code} - {self.name}'


class PurchaseOrder(models.Model):
    STATUS_CHOICES=[('draft','Bản nháp'),('approved','Đã duyệt'),('partially_received','Nhận một phần'),('received','Đã nhận đủ'),('cancelled','Đã hủy')]
    supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT,related_name='purchase_orders'); code=models.CharField(max_length=30,unique=True)
    status=models.CharField(max_length=30,choices=STATUS_CHOICES,default='draft'); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); created_at=models.DateTimeField(auto_now_add=True); note=models.CharField(max_length=255,blank=True)
    class Meta: db_table='purchase_order'; ordering=['-created_at']


class PurchaseOrderItem(models.Model):
    purchase_order=models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,related_name='items'); variant=models.ForeignKey(ProductVariant,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(); received_quantity=models.PositiveIntegerField(default=0); unit_cost=models.DecimalField(max_digits=14,decimal_places=0)
    class Meta: db_table='purchase_order_item'; constraints=[models.UniqueConstraint(fields=['purchase_order','variant'],name='unique_po_variant')]
    @property
    def remaining(self): return self.quantity-self.received_quantity


class GoodsReceipt(models.Model):
    purchase_order=models.ForeignKey(PurchaseOrder,on_delete=models.PROTECT,related_name='receipts'); warehouse=models.ForeignKey(Warehouse,on_delete=models.PROTECT)
    receipt_code=models.CharField(max_length=50,unique=True); received_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='goods_receipt'; ordering=['-created_at']


class GoodsReceiptItem(models.Model):
    receipt=models.ForeignKey(GoodsReceipt,on_delete=models.CASCADE,related_name='items'); purchase_item=models.ForeignKey(PurchaseOrderItem,on_delete=models.PROTECT); quantity=models.PositiveIntegerField()
    class Meta: db_table='goods_receipt_item'; constraints=[models.UniqueConstraint(fields=['receipt','purchase_item'],name='unique_receipt_purchase_item')]
