from django.db import models
from django.db.models import Q

from Login.models import User
from Product.models import ProductVariant


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart'
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=Q(user__isnull=False), name='unique_user_cart'),
            models.UniqueConstraint(fields=['session_key'], condition=Q(session_key__isnull=False), name='unique_session_cart'),
        ]


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField()
    price_when_added = models.DecimalField(max_digits=12, decimal_places=0)
    is_selected = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_item'
        constraints = [
            models.UniqueConstraint(fields=['cart', 'variant'], name='unique_cart_variant'),
            models.CheckConstraint(condition=Q(quantity__gt=0), name='cart_quantity_positive'),
        ]

    @property
    def unit_price(self):
        return self.variant.price * (100 - self.variant.product.discount_percent) / 100

    @property
    def line_total(self):
        return self.unit_price * self.quantity
