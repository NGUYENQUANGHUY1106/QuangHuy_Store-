from django.urls import path

from . import views


urlpatterns = [
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('account/', views.account_page, name='account'),
    path('account/change-password/', views.change_password_page, name='change_password'),
    path('account/addresses/add/', views.address_add, name='address_add'),
    path('account/addresses/<int:address_id>/edit/', views.address_edit, name='address_edit'),
    path('account/addresses/<int:address_id>/delete/', views.address_delete, name='address_delete'),
    path('account/addresses/<int:address_id>/default/', views.address_set_default, name='address_set_default'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_page, name='reset_password'),
]
