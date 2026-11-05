from django.urls import path

from . import views


urlpatterns = [
    path('checkout/', views.checkout_page, name='checkout'),
    path('checkout/success/<str:order_code>/', views.checkout_success, name='checkout_success'),
]
