from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Login.models import User
from Product.models import Product

from .models import WishlistItem


def current_user(request):
    user_id = request.session.get('user_id')
    return User.objects.filter(id=user_id).first() if user_id else None


def wishlist_page(request):
    user = current_user(request)
    if not user:
        return redirect('/login/?next=/account/wishlist/')
    items = user.wishlist_items.select_related('product', 'product__brand', 'product__category')
    return render(request, 'Engagement/Wishlist.html', {'wishlist_items': items})


@require_POST
def wishlist_toggle(request, product_id):
    user = current_user(request)
    if not user:
        return JsonResponse({'success': False, 'login_url': '/login/'}, status=401)
    product = get_object_or_404(Product, id=product_id)
    item = WishlistItem.objects.filter(user=user, product=product).first()
    if item:
        item.delete()
        added = False
    else:
        WishlistItem.objects.create(user=user, product=product)
        added = True
    return JsonResponse({'success': True, 'added': added})


def compare_page(request):
    product_ids = request.GET.getlist('ids')[:4]
    products = list(
        Product.objects.filter(id__in=product_ids, is_active=True)
        .select_related('brand', 'category').prefetch_related('variants')
    )
    error = ''
    if len(products) < 2:
        products = []
        error = 'Vui lòng chọn từ 2 đến 4 sản phẩm để so sánh.'
    elif len({product.category_id for product in products}) > 1:
        products = []
        error = 'Chỉ có thể so sánh các sản phẩm cùng danh mục.'
    return render(request, 'Engagement/Compare.html', {'compare_products': products, 'compare_error': error})
