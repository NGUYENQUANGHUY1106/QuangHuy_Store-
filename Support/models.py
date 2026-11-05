from django.db import models
from Login.models import User

class Notification(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
    title=models.CharField(max_length=200);message=models.CharField(max_length=500);link=models.CharField(max_length=255,blank=True)
    is_read=models.BooleanField(default=False);created_at=models.DateTimeField(auto_now_add=True)
    class Meta:db_table='notification';ordering=['-created_at']

class SupportTicket(models.Model):
    STATUS_CHOICES=[('open','Đang mở'),('answered','Đã trả lời'),('closed','Đã đóng')]
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='support_tickets')
    category=models.CharField(max_length=50);subject=models.CharField(max_length=200)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='open');created_at=models.DateTimeField(auto_now_add=True)
    class Meta:db_table='support_ticket';ordering=['-created_at']

class SupportMessage(models.Model):
    ticket=models.ForeignKey(SupportTicket,on_delete=models.CASCADE,related_name='messages')
    sender=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    message=models.TextField(max_length=2000);attachment=models.FileField(upload_to='support/',blank=True)
    is_staff_reply=models.BooleanField(default=False);created_at=models.DateTimeField(auto_now_add=True)
    class Meta:db_table='support_message';ordering=['created_at','id']

class FAQ(models.Model):
    question=models.CharField(max_length=300);answer=models.TextField();order=models.PositiveIntegerField(default=0);is_active=models.BooleanField(default=True)
    class Meta:db_table='faq';ordering=['order','id']
