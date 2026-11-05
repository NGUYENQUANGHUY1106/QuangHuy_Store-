from django.db import models

from Checkout.models import OrderItem
from Login.models import User
from Product.models import Product


class Review(models.Model):
    STATUS_CHOICES = [('approved', 'Đã duyệt'), ('reported', 'Bị báo cáo'), ('hidden', 'Đã ẩn')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.PROTECT, related_name='review')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='one_review_per_user_product'),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=5), name='review_rating_1_to_5'),
        ]


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')

    class Meta:
        db_table = 'review_image'


class ReviewReport(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_report'
        constraints = [models.UniqueConstraint(fields=['review', 'user'], name='one_report_per_user_review')]


class ProductQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_questions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    question = models.CharField(max_length=500)
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_question'
        ordering = ['-created_at']
