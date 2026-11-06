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
    path('catalog/categories/', views.categories, name='categories'),
    path('catalog/brands/', views.brands, name='brands'),
    path('catalog/sports/', views.sports, name='sports'),
    path('catalog/<str:kind>/add/', views.catalog_create, name='catalog_create'),
    path('catalog/<str:kind>/<int:object_id>/edit/', views.catalog_edit, name='catalog_edit'),
    path('catalog/<str:kind>/<int:object_id>/toggle/', views.catalog_toggle, name='catalog_toggle'),
]

