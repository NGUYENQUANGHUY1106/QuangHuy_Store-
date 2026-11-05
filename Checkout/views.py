import secrets
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Cart.models import CartItem
from Cart.services import get_cart
from Login.models import Address, User
from Product.models import ProductVariant

from .models import Coupon, CouponUsage, Order, OrderAddress, OrderDiscount, OrderItem, OrderStatusHistory, Promotion


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
    if coupon.used_count >= coupon.usage_limit:
        return None, Decimal('0'), 'Mã giảm giá đã hết lượt sử dụng.'
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
        if shipping_method not in {'standard', 'express'} or payment_method != 'cod':
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
                from Payment.models import Payment
                Payment.objects.create(order=order, method='cod', status='pending', amount=grand_total)
                OrderStatusHistory.objects.create(order=order, status='pending', note='Đơn hàng đã được tạo.')
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
                    locked_coupon = Coupon.objects.select_for_update().get(id=coupon.id)
                    if locked_coupon.used_count >= locked_coupon.usage_limit:
                        raise ValueError('Mã giảm giá đã hết lượt sử dụng.')
                    CouponUsage.objects.create(coupon=locked_coupon, user=user, order=order)
                    locked_coupon.used_count += 1
                    locked_coupon.save(update_fields=['used_count'])
                    OrderDiscount.objects.create(
                        order=order, coupon_code=locked_coupon.code,
                        discount_percent=locked_coupon.discount_percent, amount=discount,
                    )
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


def order_list(request):
    user = get_user(request)
    if not user:
        return redirect('/login/?next=/account/orders/')
    selected_status = request.GET.get('status', '')
    orders = Order.objects.filter(user=user).select_related('payment')
    valid_statuses = {value for value, label in Order.STATUS_CHOICES}
    if selected_status in valid_statuses:
        orders = orders.filter(status=selected_status)
    else:
        selected_status = ''
    page_obj = Paginator(orders, 10).get_page(request.GET.get('page'))
    return render(request, 'Checkout/OrderList.html', {
        'page_obj': page_obj, 'selected_status': selected_status,
        'status_choices': Order.STATUS_CHOICES,
    })


def order_detail(request, order_code):
    user = get_user(request)
    if not user:
        return redirect('login')
    order = get_object_or_404(
        Order.objects.select_related('payment', 'shipping_address').prefetch_related('items', 'status_history'),
        order_code=order_code, user=user,
    )
    return render(request, 'Checkout/OrderDetail.html', {'order': order})


def order_cancel(request, order_code):
    if request.method != 'POST':
        return redirect('order_detail', order_code=order_code)
    user = get_user(request)
    if not user:
        return redirect('login')
    with transaction.atomic():
        order = get_object_or_404(Order.objects.select_for_update(), order_code=order_code, user=user)
        if order.status not in {'pending', 'confirmed'}:
            messages.error(request, 'Đơn hàng ở trạng thái này không thể hủy.')
            return redirect('order_detail', order_code=order.order_code)
        for item in order.items.select_related('variant'):
            variant = ProductVariant.objects.select_for_update().get(id=item.variant_id)
            variant.stock += item.quantity
            variant.save(update_fields=['stock'])
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        if order.payment.status == 'pending':
            order.payment.status = 'failed'
            order.payment.save(update_fields=['status', 'updated_at'])
        usage = CouponUsage.objects.select_related('coupon').filter(order=order).first()
        if usage:
            coupon = Coupon.objects.select_for_update().get(id=usage.coupon_id)
            usage.delete()
            coupon.used_count = max(coupon.used_count - 1, 0)
            coupon.save(update_fields=['used_count'])
        OrderStatusHistory.objects.create(order=order, status='cancelled', note='Khách hàng đã hủy đơn.')
    messages.success(request, 'Đã hủy đơn hàng và hoàn lại tồn kho.')
    return redirect('order_detail', order_code=order.order_code)


def order_reorder(request, order_code):
    if request.method != 'POST':
        return redirect('order_detail', order_code=order_code)
    user = get_user(request)
    if not user:
        return redirect('login')
    order = get_object_or_404(Order.objects.prefetch_related('items__variant__product'), order_code=order_code, user=user)
    from Cart.services import add_variant
    added = 0
    skipped = []
    for old_item in order.items.all():
        variant = old_item.variant
        if not variant.is_active or not variant.product.is_active or variant.stock < 1:
            skipped.append(old_item.sku)
            continue
        quantity = min(old_item.quantity, variant.stock)
        success, message = add_variant(request, variant, quantity)
        if success:
            added += 1
        else:
            skipped.append(old_item.sku)
    if added:
        messages.success(request, f'Đã thêm lại {added} sản phẩm vào giỏ.')
    if skipped:
        messages.warning(request, 'Không thể mua lại SKU: ' + ', '.join(skipped))
    return redirect('cart_page')


def active_promotions(request):
    now = timezone.now()
    promotions = Promotion.objects.filter(is_active=True, starts_at__lte=now, ends_at__gte=now)
    return JsonResponse({'promotions': [
        {'title': item.title, 'description': item.description, 'ends_at': item.ends_at.isoformat()}
        for item in promotions
    ]})


def coupon_preview(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Chỉ hỗ trợ POST.'}, status=405)
    user = get_user(request)
    if not user:
        return JsonResponse({'error': 'Vui lòng đăng nhập.'}, status=401)
    cart = get_cart(request, create=False)
    items = [] if not cart else cart.items.filter(is_selected=True).select_related('variant', 'variant__product')
    subtotal = sum((item.line_total for item in items), Decimal('0'))
    coupon, discount, error = get_coupon(request.POST.get('coupon_code', '').strip(), user, subtotal)
    if error:
        return JsonResponse({'valid': False, 'error': error}, status=400)
    return JsonResponse({
        'valid': bool(coupon), 'subtotal': int(subtotal), 'discount': int(discount),
        'total_after_discount': int(max(subtotal - discount, Decimal('0'))),
    })
