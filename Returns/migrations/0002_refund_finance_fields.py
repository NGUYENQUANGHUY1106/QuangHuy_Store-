from django.db import migrations,models
class Migration(migrations.Migration):
    dependencies=[('Returns','0001_initial')]
    operations=[migrations.AddField(model_name='refund',name='idempotency_key',field=models.CharField(blank=True,max_length=100,null=True,unique=True)),migrations.AddField(model_name='refund',name='processed_at',field=models.DateTimeField(blank=True,null=True))]
