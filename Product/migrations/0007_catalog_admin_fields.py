from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Product', '0006_category_meta_description_category_seo_title_and_more')]
    operations = [
        migrations.AddField(model_name='category', name='description', field=models.TextField(blank=True)),
        migrations.AddField(model_name='category', name='logo', field=models.ImageField(blank=True, upload_to='categories/')),
        migrations.AddField(model_name='brand', name='logo', field=models.ImageField(blank=True, upload_to='brands/')),
        migrations.AddField(model_name='brand', name='order', field=models.PositiveIntegerField(default=0)),
        migrations.CreateModel(
            name='SportType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=120, unique=True)),
                ('description', models.TextField(blank=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'db_table': 'sport_type', 'ordering': ['order', 'name']},
        ),
    ]
