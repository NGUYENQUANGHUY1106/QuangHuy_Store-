from django.urls import path

from . import views


urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('checkout/success/<str:order_code>/', views.checkout_success, name='checkout_success'),
    path('account/orders/', views.order_list, name='order_list'),
    path('account/orders/<str:order_code>/', views.order_detail, name='order_detail'),
    path('account/orders/<str:order_code>/cancel/', views.order_cancel, name='order_cancel'),
    path('account/orders/<str:order_code>/reorder/', views.order_reorder, name='order_reorder'),
]
