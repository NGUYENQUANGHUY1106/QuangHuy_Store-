from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Banner, Category, Product


def home_page(request, category_slug=None):
    products = Product.objects.filter(is_active=True).select_related('category', 'brand')
    selected_category = None
    search_query = request.GET.get('q', '').strip()

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    if request.GET.get('new') == '1':
        products = products.filter(is_new=True)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(brand__name__icontains=search_query)
        )

    paginator = Paginator(products, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    now = timezone.now()
    banner = Banner.objects.filter(is_active=True).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now),
        Q(ends_at__isnull=True) | Q(ends_at__gte=now),
    ).first()

    active_products = Product.objects.filter(is_active=True).select_related('category', 'brand')

    return render(request, 'Product/Home.html', {
        'banner': banner,
        'featured_categories': Category.objects.filter(is_active=True, is_featured=True)[:6],
        'new_products': active_products.filter(is_new=True)[:6],
        'best_sellers': active_products.filter(is_best_seller=True)[:6],
        'promotion_products': active_products.filter(discount_percent__gt=0)[:6],
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_category': selected_category,
    })


def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images'),
        slug=product_slug,
        is_active=True,
    )
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
    ).exclude(id=product.id).select_related('category', 'brand')[:4]

    return render(request, 'Product/Detail.html', {
        'product': product,
        'related_products': related_products,
    })


def information_page(request, page_slug):
    pages = {
        'lien-he': {
            'title': 'Liên hệ QuangHuy Store',
            'content': 'Hotline: 0900 000 000 · Email: support@quanghuystore.vn',
        },
        'chinh-sach': {
            'title': 'Chính sách mua hàng',
            'content': 'Hỗ trợ kiểm tra sản phẩm và đổi size trong vòng 7 ngày.',
        },
        'huong-dan-size': {
            'title': 'Hướng dẫn chọn size',
            'content': 'Đo chiều dài bàn chân và đối chiếu size EU trước khi đặt giày.',
        },
    }
    page = pages.get(page_slug)
    if page is None:
        raise Http404('Trang thông tin không tồn tại.')
    page = {'slug': page_slug, **page}
    return render(request, 'Product/Information.html', {'page': page})
