from .models import Category
from Cart.services import cart_count_for_request, get_cart


def categories_menu(request):
    cart = get_cart(request, create=False)
    mini_cart_items = []
    if cart:
        mini_cart_items = cart.items.select_related('variant', 'variant__product')[:3]
    return {
        'menu_categories': Category.objects.filter(is_active=True, parent__isnull=True),
        'cart_count': cart_count_for_request(request),
        'mini_cart_items': mini_cart_items,
    }
