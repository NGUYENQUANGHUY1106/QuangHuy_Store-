from django.db import migrations,models
CHOICES=[('pending','Chờ xác nhận'),('confirmed','Đã xác nhận'),('packing','Đang đóng gói'),('shipped','Đã bàn giao'),('shipping','Đang giao'),('delivered','Đã giao'),('completed','Hoàn tất'),('cancelled','Đã hủy')]
class Migration(migrations.Migration):
    dependencies=[('Checkout','0005_promotion_coupon_usage_limit_coupon_used_count_and_more')]
    operations=[migrations.AlterField(model_name='order',name='status',field=models.CharField(choices=CHOICES,default='pending',max_length=20)),migrations.AlterField(model_name='orderstatushistory',name='status',field=models.CharField(choices=CHOICES,max_length=20))]
