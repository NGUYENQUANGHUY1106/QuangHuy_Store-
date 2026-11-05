from django.urls import path

from . import views


urlpatterns = [
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('account/', views.account_page, name='account'),
    path('forgot-password/', views.forgot_password_page, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_page, name='reset_password'),
]
