import django.db.models.deletion
from django.db import migrations,models
class Migration(migrations.Migration):
    dependencies=[('Payment','0001_initial')]
    operations=[migrations.CreateModel(name='PaymentTransaction',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('event_id',models.CharField(max_length=100,unique=True)),('provider_ref',models.CharField(blank=True,max_length=100)),('transaction_type',models.CharField(default='capture',max_length=20)),('status',models.CharField(max_length=20)),('amount',models.DecimalField(decimal_places=0,max_digits=14)),('created_at',models.DateTimeField(auto_now_add=True)),('payment',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='transactions',to='Payment.payment'))],options={'db_table':'payment_transaction','ordering':['-created_at']})]
