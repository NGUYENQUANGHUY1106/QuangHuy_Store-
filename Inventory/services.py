from django.core.exceptions import ValidationError
from django.db import models, transaction

from .models import GoodsReceipt,GoodsReceiptItem,PurchaseOrder,PurchaseOrderItem,Stock,StockMovement


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


@transaction.atomic
def receive_purchase_item(purchase_item_id, warehouse, quantity, receipt_code, actor):
    existing=GoodsReceipt.objects.filter(receipt_code=receipt_code).first()
    if existing: return existing, False
    item=PurchaseOrderItem.objects.select_for_update().select_related('purchase_order','variant').get(pk=purchase_item_id)
    order=PurchaseOrder.objects.select_for_update().get(pk=item.purchase_order_id)
    if order.status not in ['approved','partially_received']: raise ValidationError('Phiếu mua chưa được duyệt hoặc đã kết thúc.')
    if quantity<=0 or quantity>item.remaining: raise ValidationError('Số lượng nhận không hợp lệ.')
    receipt=GoodsReceipt.objects.create(purchase_order=order,warehouse=warehouse,receipt_code=receipt_code,received_by=actor)
    GoodsReceiptItem.objects.create(receipt=receipt,purchase_item=item,quantity=quantity)
    stock,_=Stock.objects.select_for_update().get_or_create(warehouse=warehouse,variant=item.variant,defaults={'on_hand':0})
    before=stock.on_hand; stock.on_hand+=quantity; stock.save(update_fields=['on_hand','updated_at'])
    item.received_quantity+=quantity; item.save(update_fields=['received_quantity'])
    StockMovement.objects.create(stock=stock,movement_type='receipt',quantity=quantity,before_quantity=before,after_quantity=stock.on_hand,reason=f'Nhập {order.code}',actor=actor,reference=receipt_code)
    remaining=order.items.filter(received_quantity__lt=models.F('quantity')).exists()
    order.status='partially_received' if remaining else 'received'; order.save(update_fields=['status'])
    item.variant.stock=sum(s.available for s in Stock.objects.filter(variant=item.variant,warehouse__is_online=True,warehouse__is_active=True)); item.variant.save(update_fields=['stock'])
    return receipt, True
