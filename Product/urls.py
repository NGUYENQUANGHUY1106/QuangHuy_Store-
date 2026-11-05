from django.urls import path

from . import views


urlpatterns = [
    path('', views.home_page, name='home'),
    path('products/', views.search_page, name='product_search'),
    path('products/suggest/', views.search_suggest, name='product_suggest'),
    path('category/<slug:category_slug>/', views.category_page, name='product_by_category'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:product_slug>/variants/', views.product_variants, name='product_variants'),
    path('product/<slug:product_slug>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('thong-tin/<slug:page_slug>/', views.information_page, name='information_page'),
]
