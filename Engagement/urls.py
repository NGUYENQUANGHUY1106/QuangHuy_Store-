from django.urls import path

from . import views


urlpatterns = [
    path('account/wishlist/', views.wishlist_page, name='wishlist'),
    path('account/wishlist/toggle/<int:product_id>/', views.wishlist_toggle, name='wishlist_toggle'),
    path('products/compare/', views.compare_page, name='product_compare'),
]
