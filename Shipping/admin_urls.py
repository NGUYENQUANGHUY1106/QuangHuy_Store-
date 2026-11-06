from django.urls import path
from . import admin_views as views
app_name='shipping_admin'
urlpatterns=[path('',views.dashboard,name='dashboard'),path('add/<str:kind>/',views.create_object,name='create'),path('<int:shipment_id>/events/',views.add_event,name='add_event')]
