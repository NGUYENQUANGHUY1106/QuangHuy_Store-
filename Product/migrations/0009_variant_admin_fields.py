from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Product', '0008_product_admin_fields')]
    operations = [
        migrations.AddField(model_name='productvariant', name='barcode', field=models.CharField(blank=True, max_length=80, null=True, unique=True)),
        migrations.AddField(model_name='productvariant', name='sale_price', field=models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
        migrations.AddField(model_name='productvariant', name='sale_starts_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='productvariant', name='sale_ends_at', field=models.DateTimeField(blank=True, null=True)),
    ]
