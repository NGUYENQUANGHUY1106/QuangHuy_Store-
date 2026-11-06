from django.urls import path

from . import views


app_name = 'admin_panel'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('me/', views.admin_me, name='me'),
    path('change-password/', views.change_password, name='change_password'),
    path('permission-test/', views.permission_test, name='permission_test'),
    path('403/', views.forbidden, name='forbidden'),
    path('catalog/categories/', views.categories, name='categories'),
    path('catalog/brands/', views.brands, name='brands'),
    path('catalog/sports/', views.sports, name='sports'),
    path('catalog/<str:kind>/add/', views.catalog_create, name='catalog_create'),
    path('catalog/<str:kind>/<int:object_id>/edit/', views.catalog_edit, name='catalog_edit'),
    path('catalog/<str:kind>/<int:object_id>/toggle/', views.catalog_toggle, name='catalog_toggle'),
    path('products/', views.products, name='products'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/export/', views.product_export, name='product_export'),
    path('products/bulk-hide/', views.product_bulk_hide, name='product_bulk_hide'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/publish/', views.product_publish, name='product_publish'),
    path('products/<int:product_id>/archive/', views.product_archive, name='product_archive'),
    path('products/<int:product_id>/images/add/', views.product_image_add, name='product_image_add'),
    path('product-images/<int:image_id>/delete/', views.product_image_delete, name='product_image_delete'),
]

