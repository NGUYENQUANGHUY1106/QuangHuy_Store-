from django.urls import path

from . import views


urlpatterns = [
    path('payments/<str:order_code>/status/', views.payment_status, name='payment_status'),
]
