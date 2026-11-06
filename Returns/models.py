from django.db import models
from Checkout.models import Order,OrderItem
from Login.models import User

class ReturnRequest(models.Model):
    TYPE_CHOICES=[('return','Trả hàng'),('exchange','Đổi hàng')]
    STATUS_CHOICES=[('pending','Chờ xử lý'),('reviewing','Đang xem xét'),('approved','Đã duyệt'),('rejected','Từ chối'),('received','Đã nhận hàng'),('refunded','Đã hoàn tiền'),('replaced','Đã đổi hàng')]
    user=models.ForeignKey(User,on_delete=models.PROTECT,related_name='return_requests')
    order=models.ForeignKey(Order,on_delete=models.PROTECT,related_name='return_requests')
    request_type=models.CharField(max_length=20,choices=TYPE_CHOICES)
    reason=models.CharField(max_length=500)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    admin_note=models.CharField(max_length=500,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='return_request';ordering=['-created_at']

class ReturnItem(models.Model):
    return_request=models.ForeignKey(ReturnRequest,on_delete=models.CASCADE,related_name='items')
    order_item=models.ForeignKey(OrderItem,on_delete=models.PROTECT,related_name='return_items')
    quantity=models.PositiveIntegerField()
    class Meta: db_table='return_item'

class ReturnEvidence(models.Model):
    return_request=models.ForeignKey(ReturnRequest,on_delete=models.CASCADE,related_name='evidence')
    image=models.ImageField(upload_to='returns/')
    class Meta: db_table='return_evidence'

class Refund(models.Model):
    return_request=models.OneToOneField(ReturnRequest,on_delete=models.PROTECT,related_name='refund')
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    status=models.CharField(max_length=20,default='pending')
    idempotency_key=models.CharField(max_length=100,unique=True,null=True,blank=True)
    processed_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='refund'
