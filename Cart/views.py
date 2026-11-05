from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from Product.models import ProductVariant

from .models import CartItem
from .services import add_variant, get_cart


def cart_page(request):
    cart = get_cart(request)
    items = list(cart.items.select_related('variant', 'variant__product', 'variant__product__brand'))
    for item in items:
        item.stock_error = not item.variant.is_active or not item.variant.product.is_active or item.quantity > item.variant.stock
        item.price_changed = item.price_when_added != item.unit_price
    total = sum((item.line_total for item in items if item.is_selected and not item.stock_error), 0)
    return render(request, 'Cart/Cart.html', {'cart_items': items, 'cart_total': total})


@require_POST
def cart_add(request):
    next_url = request.POST.get('next', '')
    if not next_url.startswith('/') or next_url.startswith('//'):
        next_url = reverse('cart_page')
    try:
        variant_id = int(request.POST.get('variant_id', ''))
        quantity = int(request.POST.get('quantity', '1'))
    except (TypeError, ValueError):
        messages.error(request, 'Biến thể hoặc số lượng không hợp lệ.')
        return redirect(next_url)
    variant = get_object_or_404(ProductVariant.objects.select_related('product'), id=variant_id)
    if quantity < 1 or not variant.is_active or not variant.product.is_active:
        messages.error(request, 'Sản phẩm không còn được bán hoặc số lượng không hợp lệ.')
    else:
        success, message = add_variant(request, variant, quantity)
        (messages.success if success else messages.error)(request, message)
    return redirect(next_url)


@require_POST
def cart_item_update(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem.objects.select_related('variant'), id=item_id, cart=cart)
    try:
        quantity = int(request.POST.get('quantity', ''))
    except (TypeError, ValueError):
        quantity = 0
    if quantity < 1 or quantity > item.variant.stock or not item.variant.is_active:
        messages.error(request, f'Số lượng phải từ 1 đến {item.variant.stock}.')
    else:
        with transaction.atomic():
            locked = CartItem.objects.select_for_update().get(id=item.id)
            locked.quantity = quantity
            locked.save(update_fields=['quantity', 'updated_at'])
        messages.success(request, 'Đã cập nhật số lượng.')
    return redirect('cart_page')


@require_POST
def cart_item_delete(request, item_id):
    cart = get_cart(request)
    get_object_or_404(CartItem, id=item_id, cart=cart).delete()
    messages.success(request, 'Đã xóa sản phẩm khỏi giỏ.')
    return redirect('cart_page')


@require_POST
def cart_item_select(request, item_id):
    cart = get_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.is_selected = request.POST.get('is_selected') == 'on'
    item.save(update_fields=['is_selected'])
    return redirect('cart_page')


@require_POST
def cart_clear(request):
    get_cart(request).items.all().delete()
    messages.success(request, 'Đã xóa toàn bộ giỏ hàng.')
    return redirect('cart_page')
