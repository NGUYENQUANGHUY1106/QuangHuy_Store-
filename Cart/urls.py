from django.urls import path

from . import views


urlpatterns = [
    path('cart/', views.cart_page, name='cart_page'),
    path('cart/items/add/', views.cart_add, name='cart_add'),
    path('cart/items/<int:item_id>/update/', views.cart_item_update, name='cart_item_update'),
    path('cart/items/<int:item_id>/delete/', views.cart_item_delete, name='cart_item_delete'),
    path('cart/items/<int:item_id>/select/', views.cart_item_select, name='cart_item_select'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
]
