from django.db import models
from django.utils.text import slugify


def vietnamese_slug(value):
    return slugify(value.replace('đ', 'd').replace('Đ', 'D'))


class Category(models.Model):
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='children',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='categories/', blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        db_table = 'category'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'brand'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SportType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sport_type'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [('draft', 'Bản nháp'), ('published', 'Đã công bố'), ('archived', 'Đã ẩn')]
    GENDER_CHOICES = [
        ('unisex', 'Unisex'),
        ('men', 'Nam'),
        ('women', 'Nữ'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True,
        blank=True,
    )
    sport_type = models.ForeignKey(SportType, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    image = models.ImageField(upload_to='products/')
    description = models.CharField(max_length=255, blank=True)
    material = models.CharField(max_length=100, blank=True, default='Chất liệu thể thao')
    size_guide = models.TextField(blank=True)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    is_new = models.BooleanField(default=True)
    is_best_seller = models.BooleanField(default=False)
    discount_percent = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    popularity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product'
        ordering = ['-created_at', 'id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = vietnamese_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def sale_price(self):
        if not self.discount_percent:
            return self.price
        return self.price * (100 - self.discount_percent) / 100


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=80, unique=True)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    image = models.ImageField(upload_to='products/variants/', blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'product_variant'
        ordering = ['price', 'size', 'color']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size', 'color'],
                name='unique_product_size_color',
            ),
        ]

    def __str__(self):
        return f'{self.product.name} - {self.size} - {self.color}'

    @property
    def in_stock(self):
        return self.is_active and self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'product_image'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Ảnh {self.product.name}'


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = 'product_specification'
        ordering = ['id']


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/', blank=True)
    link_text = models.CharField(max_length=100, default='KHÁM PHÁ SẢN PHẨM')
    link_url = models.CharField(max_length=255, default='#products')
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'banner'
        ordering = ['order', '-id']

    def __str__(self):
        return self.title
