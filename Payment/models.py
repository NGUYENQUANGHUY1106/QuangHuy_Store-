from django.db import models

from Checkout.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [('pending', 'Chờ thu tiền'), ('paid', 'Đã thanh toán'), ('failed', 'Thất bại')]

    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='payment')
    method = models.CharField(max_length=20, default='cod')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment'


class PaymentTransaction(models.Model):
    payment=models.ForeignKey(Payment,on_delete=models.PROTECT,related_name='transactions')
    event_id=models.CharField(max_length=100,unique=True); provider_ref=models.CharField(max_length=100,blank=True)
    transaction_type=models.CharField(max_length=20,default='capture'); status=models.CharField(max_length=20); amount=models.DecimalField(max_digits=14,decimal_places=0)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: db_table='payment_transaction'; ordering=['-created_at']
