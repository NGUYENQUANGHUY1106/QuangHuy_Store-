from django.urls import path

from . import views
from . import views_operations as operations


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
    path('products/<int:product_id>/variants/', views.variants, name='variants'),
    path('products/<int:product_id>/variants/add/', views.variant_form, name='variant_add'),
    path('products/<int:product_id>/variants/<int:variant_id>/edit/', views.variant_form, name='variant_edit'),
    path('products/<int:product_id>/variants/<int:variant_id>/toggle/', views.variant_toggle, name='variant_toggle'),
    path('orders/',views.orders,name='orders'),
    path('orders/<int:order_id>/',views.order_detail_admin,name='order_detail'),
    path('orders/<int:order_id>/<str:action>/',views.order_action,name='order_action'),
    path('returns/', operations.returns_list, name='returns'),
    path('returns/<int:return_id>/', operations.return_detail, name='return_detail'),
    path('returns/<int:return_id>/<str:action>/', operations.return_action, name='return_action'),
    path('customers/', operations.customers, name='customers'),
    path('customers/<int:customer_id>/toggle/', operations.customer_toggle, name='customer_toggle'),
    path('staff/', operations.staff_list, name='staff'),
    path('staff/add/', operations.staff_form, name='staff_add'),
    path('staff/<int:user_id>/edit/', operations.staff_form, name='staff_edit'),
    path('marketing/', operations.marketing, name='marketing'),
    path('content/', operations.content, name='content'),
    path('operations/<str:kind>/add/', operations.crud_form, name='operation_add'),
    path('operations/<str:kind>/<int:object_id>/edit/', operations.crud_form, name='operation_edit'),
    path('support/', operations.support_queue, name='support'),
    path('reviews/<int:review_id>/moderate/', operations.review_moderate, name='review_moderate'),
    path('tickets/<int:ticket_id>/action/', operations.ticket_action, name='ticket_action'),
    path('reports/', operations.reports, name='reports'),
    path('reports/export/', operations.reports_export, name='reports_export'),
    path('settings/', operations.settings_page, name='settings'),
    path('audit-logs/', operations.audit_logs, name='audit_logs'),
]

