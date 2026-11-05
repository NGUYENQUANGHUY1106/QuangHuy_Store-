import secrets
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Cart.models import CartItem
from Cart.services import get_cart
from Login.models import Address, User
from Product.models import ProductVariant

from .models import Coupon, CouponUsage, Order, OrderAddress, OrderItem


def get_user(request):
    user_id = request.session.get('user_id')
    return User.objects.filter(id=user_id).first() if user_id else None


def get_coupon(code, user, subtotal):
    if not code:
        return None, Decimal('0'), ''
    now = timezone.now()
    coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
    if not coupon:
        return None, Decimal('0'), 'Mã giảm giá không hợp lệ.'
    if coupon.starts_at and coupon.starts_at > now:
        return None, Decimal('0'), 'Mã giảm giá chưa bắt đầu.'
    if coupon.ends_at and coupon.ends_at < now:
        return None, Decimal('0'), 'Mã giảm giá đã hết hạn.'
    if subtotal < coupon.min_order:
        return None, Decimal('0'), 'Đơn hàng chưa đạt giá trị tối thiểu của mã.'
    if CouponUsage.objects.filter(coupon=coupon, user=user).exists():
        return None, Decimal('0'), 'Bạn đã sử dụng mã giảm giá này.'
    discount = subtotal * coupon.discount_percent / 100
    return coupon, discount, ''


def checkout_page(request):
    user = get_user(request)
    if not user:
        return redirect('/login/?next=/checkout/')

    cart = get_cart(request, create=False)
    items = [] if not cart else list(
        cart.items.filter(is_selected=True).select_related('variant', 'variant__product')
    )
    subtotal = sum((item.line_total for item in items), Decimal('0'))

    if request.method == 'POST':
        address = get_object_or_404(Address, id=request.POST.get('address_id'), user=user)
        shipping_method = request.POST.get('shipping_method', 'standard')
        payment_method = request.POST.get('payment_method', 'cod')
        idempotency_key = request.POST.get('idempotency_key', '')
        coupon_code = request.POST.get('coupon_code', '').strip().upper()

        old_order = Order.objects.filter(idempotency_key=idempotency_key, user=user).first()
        if old_order:
            return redirect('checkout_success', order_code=old_order.order_code)
        if not idempotency_key or idempotency_key != request.session.get('checkout_key'):
            messages.error(request, 'Phiên thanh toán không hợp lệ. Vui lòng thử lại.')
            return redirect('checkout')
        if not items:
            messages.error(request, 'Bạn chưa chọn sản phẩm để thanh toán.')
            return redirect('cart_page')
        if shipping_method not in {'standard', 'express'} or payment_method not in {'cod', 'online'}:
            messages.error(request, 'Phương thức vận chuyển hoặc thanh toán không hợp lệ.')
            return redirect('checkout')
        coupon, discount, coupon_error = get_coupon(coupon_code, user, subtotal)
        if coupon_error:
            messages.error(request, coupon_error)
            return redirect('checkout')

        shipping_fee = Decimal('60000') if shipping_method == 'express' else Decimal('30000')
        if shipping_method == 'standard' and subtotal >= Decimal('999000'):
            shipping_fee = Decimal('0')
        grand_total = max(subtotal - discount + shipping_fee, Decimal('0'))

        try:
            with transaction.atomic():
                locked_variants = {}
                for item in items:
                    variant = ProductVariant.objects.select_for_update().select_related('product').get(id=item.variant_id)
                    if not variant.is_active or not variant.product.is_active or variant.stock < item.quantity:
                        raise ValueError(f'{variant.sku} không đủ tồn kho.')
                    locked_variants[item.id] = variant

                order = Order.objects.create(
                    user=user, order_code='QH' + secrets.token_hex(5).upper(),
                    idempotency_key=idempotency_key, payment_method=payment_method,
                    shipping_method=shipping_method, subtotal=subtotal, discount=discount,
                    shipping_fee=shipping_fee, grand_total=grand_total,
                    coupon_code=coupon.code if coupon else '', note=request.POST.get('note', '').strip()[:500],
                )
                OrderAddress.objects.create(
                    order=order, recipient_name=address.recipient_name, phone=address.phone,
                    province=address.province, ward=address.ward, detail=address.detail,
                )
                for item in items:
                    variant = locked_variants[item.id]
                    unit_price = item.unit_price
                    OrderItem.objects.create(
                        order=order, variant=variant, product_name=variant.product.name,
                        sku=variant.sku, size=variant.size, color=variant.color,
                        unit_price=unit_price, quantity=item.quantity,
                        line_total=unit_price * item.quantity,
                    )
                    variant.stock -= item.quantity
                    variant.save(update_fields=['stock'])
                if coupon:
                    CouponUsage.objects.create(coupon=coupon, user=user, order=order)
                address.is_used_in_order = True
                address.save(update_fields=['is_used_in_order'])
                CartItem.objects.filter(id__in=[item.id for item in items]).delete()
        except ValueError as error:
            messages.error(request, str(error))
            return redirect('cart_page')

        request.session.pop('checkout_key', None)
        return redirect('checkout_success', order_code=order.order_code)

    checkout_key = request.session.get('checkout_key') or secrets.token_hex(32)
    request.session['checkout_key'] = checkout_key
    return render(request, 'Checkout/Checkout.html', {
        'checkout_items': items, 'subtotal': subtotal,
        'addresses': user.addresses.all(), 'checkout_key': checkout_key,
    })


def checkout_success(request, order_code):
    user = get_user(request)
    if not user:
        return redirect('login')
    order = get_object_or_404(Order.objects.prefetch_related('items'), order_code=order_code, user=user)
    return render(request, 'Checkout/Success.html', {'order': order})
