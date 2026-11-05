from django.urls import path
from . import views
urlpatterns=[path('shipping/options/',views.shipping_options,name='shipping_options'),path('account/orders/<str:order_code>/shipment/',views.shipment_status,name='shipment_status')]
