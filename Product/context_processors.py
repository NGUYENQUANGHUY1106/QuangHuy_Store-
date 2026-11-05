from .models import Category
from Cart.services import cart_count_for_request, get_cart


def categories_menu(request):
    cart = get_cart(request, create=False)
    mini_cart_items = []
    if cart:
        mini_cart_items = cart.items.select_related('variant', 'variant__product')[:3]
    wishlist_product_ids = []
    user_id = request.session.get('user_id')
    if user_id:
        from Engagement.models import WishlistItem
        wishlist_product_ids = list(WishlistItem.objects.filter(user_id=user_id).values_list('product_id', flat=True))
    return {
        'menu_categories': Category.objects.filter(is_active=True, parent__isnull=True),
        'cart_count': cart_count_for_request(request),
        'mini_cart_items': mini_cart_items,
        'wishlist_product_ids': wishlist_product_ids,
        'canonical_url': request.build_absolute_uri(request.path),
        'seo_robots': 'noindex, nofollow' if request.path.startswith(('/account/', '/cart/', '/checkout/', '/support/')) else 'index, follow',
    }
