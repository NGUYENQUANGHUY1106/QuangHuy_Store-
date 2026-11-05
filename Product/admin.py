from django.contrib import admin

from .models import Banner, Brand, Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'is_featured', 'is_active']
    list_editable = ['order', 'is_featured', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'gender', 'price', 'is_new', 'is_best_seller', 'is_active']
    list_filter = ['brand', 'category', 'gender', 'is_new', 'is_best_seller', 'is_active']
    search_fields = ['name', 'variants__sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'starts_at', 'ends_at', 'is_active']
    list_editable = ['order', 'is_active']
