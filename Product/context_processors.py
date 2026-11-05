from .models import Category


def categories_menu(request):
    return {
        'menu_categories': Category.objects.filter(is_active=True, parent__isnull=True),
        'cart_count': request.session.get('cart_count', 0),
    }
