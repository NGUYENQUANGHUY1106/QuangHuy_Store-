from django.urls import path
from . import views

urlpatterns = [
    path('reviews/product/<int:product_id>/create/', views.review_create, name='review_create'),
    path('reviews/<int:review_id>/edit/', views.review_edit, name='review_edit'),
    path('reviews/<int:review_id>/delete/', views.review_delete, name='review_delete'),
    path('reviews/<int:review_id>/report/', views.review_report, name='review_report'),
    path('questions/product/<int:product_id>/create/', views.question_create, name='question_create'),
]
