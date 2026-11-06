from django.urls import path
from . import admin_views as views
app_name='finance_admin'
urlpatterns=[path('',views.dashboard,name='dashboard'),path('payments/<int:payment_id>/cod-paid/',views.mark_cod_paid,name='mark_cod_paid'),path('returns/<int:return_id>/refund/',views.create_refund,name='create_refund')]
