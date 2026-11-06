from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Stock, StockMovement


@transaction.atomic
def adjust_stock(stock_id, new_quantity, reason, actor, reference=''):
    stock = Stock.objects.select_for_update().select_related('variant').get(pk=stock_id)
    if new_quantity < stock.reserved:
        raise ValidationError('Tồn thực tế không được nhỏ hơn số lượng đang giữ.')
    before = stock.on_hand
    stock.on_hand = new_quantity
    stock.save(update_fields=['on_hand','updated_at'])
    stock.variant.stock = sum(item.on_hand - item.reserved for item in Stock.objects.filter(variant=stock.variant, warehouse__is_online=True, warehouse__is_active=True))
    stock.variant.save(update_fields=['stock'])
    StockMovement.objects.create(stock=stock, movement_type='adjustment', quantity=new_quantity-before, before_quantity=before, after_quantity=new_quantity, reason=reason, actor=actor, reference=reference)
    return stock
