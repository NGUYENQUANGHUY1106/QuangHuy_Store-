from django.urls import path

from . import views


app_name = 'admin_panel'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('me/', views.admin_me, name='me'),
    path('change-password/', views.change_password, name='change_password'),
    path('permission-test/', views.permission_test, name='permission_test'),
    path('403/', views.forbidden, name='forbidden'),
]

