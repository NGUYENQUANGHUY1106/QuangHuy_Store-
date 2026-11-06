from django.urls import path
from . import views
app_name='inventory'
urlpatterns=[path('',views.stock_list,name='stock_list'),path('warehouses/add/',views.warehouse_create,name='warehouse_create'),path('stocks/add/',views.stock_create,name='stock_create'),path('stocks/<int:stock_id>/adjust/',views.stock_adjust,name='stock_adjust'),path('counts/add/',views.count_create,name='count_create'),path('counts/<int:count_id>/complete/',views.count_complete,name='count_complete')]
