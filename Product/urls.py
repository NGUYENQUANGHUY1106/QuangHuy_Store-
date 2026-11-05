from django.urls import path

from . import views


urlpatterns = [
    path('', views.home_page, name='home'),
    path('category/<slug:category_slug>/', views.category_page, name='product_by_category'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('thong-tin/<slug:page_slug>/', views.information_page, name='information_page'),
]
