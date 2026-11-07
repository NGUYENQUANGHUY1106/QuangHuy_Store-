from django.conf import settings
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
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='assigned_tickets')
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

class StaticPage(models.Model):
    title=models.CharField(max_length=200);slug=models.SlugField(max_length=100,unique=True);content=models.TextField();meta_description=models.CharField(max_length=160,blank=True);is_active=models.BooleanField(default=True);updated_at=models.DateTimeField(auto_now=True)
    class Meta:db_table='static_page'

class SiteSettings(models.Model):
    store_name=models.CharField(max_length=100,default='QuangHuy Store');contact_email=models.EmailField(default='support@quanghuystore.vn');hotline=models.CharField(max_length=20,default='0900 000 000');address=models.CharField(max_length=255,blank=True)
    shipping_fee=models.DecimalField(max_digits=12,decimal_places=0,default=30000)
    free_shipping_min=models.DecimalField(max_digits=14,decimal_places=0,default=999000)
    low_stock_threshold=models.PositiveIntegerField(default=5)
    allow_checkout=models.BooleanField(default=True)
    version=models.PositiveIntegerField(default=1)
    class Meta:db_table='site_settings';verbose_name_plural='Site settings'

class BlogPost(models.Model):
    STATUS_CHOICES=[('draft','Bản nháp'),('published','Đã đăng')]
    title=models.CharField(max_length=200)
    slug=models.SlugField(max_length=150,unique=True)
    summary=models.CharField(max_length=300,blank=True)
    content=models.TextField()
    meta_description=models.CharField(max_length=160,blank=True)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')
    published_at=models.DateTimeField(null=True,blank=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:db_table='blog_post';ordering=['-published_at','-id']

class SystemEvent(models.Model):
    level=models.CharField(max_length=20,default='info')
    source=models.CharField(max_length=100)
    message=models.CharField(max_length=500)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:db_table='system_event';ordering=['-created_at']
