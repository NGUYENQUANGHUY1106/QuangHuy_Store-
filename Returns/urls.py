from django.urls import path
from . import views
urlpatterns=[path('account/returns/',views.return_list,name='return_list'),path('account/orders/<str:order_code>/return/',views.return_create,name='return_create'),path('account/returns/<int:request_id>/',views.return_detail,name='return_detail')]
