from django.db import transaction
from django.db.models import Sum

from .models import Cart, CartItem


def current_price(variant):
    return variant.price * (100 - variant.product.discount_percent) / 100


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def get_cart(request, create=True):
    user_id = request.session.get('user_id')
    if user_id:
        if create:
            cart, created = Cart.objects.get_or_create(user_id=user_id)
            return cart
        return Cart.objects.filter(user_id=user_id).first()

    session_key = ensure_session_key(request)
    if create:
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    return Cart.objects.filter(session_key=session_key).first()


def add_variant(request, variant, quantity):
    cart = get_cart(request)
    with transaction.atomic():
        Cart.objects.select_for_update().get(id=cart.id)
        item = CartItem.objects.select_for_update().filter(cart=cart, variant=variant).first()
        new_quantity = quantity + (item.quantity if item else 0)
        if new_quantity > variant.stock:
            return False, f'Sản phẩm chỉ còn {variant.stock} trong kho.'
        if item:
            item.quantity = new_quantity
            item.save(update_fields=['quantity', 'updated_at'])
        else:
            CartItem.objects.create(
                cart=cart, variant=variant, quantity=quantity,
                price_when_added=current_price(variant),
            )
    return True, 'Đã thêm sản phẩm vào giỏ hàng.'


def cart_count_for_request(request):
    cart = get_cart(request, create=False)
    if cart is None:
        return 0
    return cart.items.aggregate(total=Sum('quantity'))['total'] or 0


def merge_guest_cart(user, guest_session_key, legacy_cart=None):
    user_cart, _ = Cart.objects.get_or_create(user=user)
    guest_cart = Cart.objects.filter(session_key=guest_session_key).first() if guest_session_key else None
    with transaction.atomic():
        if guest_cart:
            for guest_item in guest_cart.items.select_related('variant', 'variant__product'):
                item = CartItem.objects.filter(cart=user_cart, variant=guest_item.variant).first()
                quantity = min((item.quantity if item else 0) + guest_item.quantity, guest_item.variant.stock)
                if quantity > 0:
                    CartItem.objects.update_or_create(
                        cart=user_cart, variant=guest_item.variant,
                        defaults={'quantity': quantity, 'price_when_added': current_price(guest_item.variant)},
                    )
            guest_cart.delete()
        if legacy_cart:
            from Product.models import ProductVariant
            for variant_id, legacy_quantity in legacy_cart.items():
                variant = ProductVariant.objects.filter(id=variant_id, is_active=True).first()
                if variant:
                    item = CartItem.objects.filter(cart=user_cart, variant=variant).first()
                    quantity = min((item.quantity if item else 0) + int(legacy_quantity), variant.stock)
                    if quantity > 0:
                        CartItem.objects.update_or_create(
                            cart=user_cart, variant=variant,
                            defaults={'quantity': quantity, 'price_when_added': current_price(variant)},
                        )
    return user_cart
