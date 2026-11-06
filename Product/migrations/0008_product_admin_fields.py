import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Product', '0007_catalog_admin_fields')]
    operations = [
        migrations.AddField(model_name='product', name='size_guide', field=models.TextField(blank=True)),
        migrations.AddField(model_name='product', name='status', field=models.CharField(choices=[('draft','Bản nháp'),('published','Đã công bố'),('archived','Đã ẩn')], default='published', max_length=20)),
        migrations.AddField(model_name='product', name='sport_type', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='Product.sporttype')),
        migrations.CreateModel(name='ProductSpecification', fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=100)),('value',models.CharField(max_length=255)),('product',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='specifications',to='Product.product'))], options={'db_table':'product_specification','ordering':['id']}),
    ]
