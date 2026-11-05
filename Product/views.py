from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Banner, Brand, Category, Product, ProductVariant


def active_products():
    return Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).filter(
        Q(brand__isnull=True) | Q(brand__is_active=True),
    ).select_related('category', 'brand').annotate(
        variant_min_price=Min(
            'variants__price',
            filter=Q(variants__is_active=True),
        ),
    ).order_by('-created_at', 'id')


def category_and_children_ids(category):
    category_ids = [category.id]
    pending_ids = [category.id]

    while pending_ids:
        child_ids = list(
            Category.objects.filter(
                parent_id__in=pending_ids,
                is_active=True,
            ).values_list('id', flat=True)
        )
        category_ids.extend(child_ids)
        pending_ids = child_ids

    return category_ids


def parse_price(value, label, errors):
    if value == '':
        return None
    try:
        price = Decimal(value)
    except InvalidOperation:
        errors.append(f'{label} không hợp lệ.')
        return None
    if not price.is_finite() or price < 0 or price > Decimal('999999999999'):
        errors.append(f'{label} phải nằm trong khoảng từ 0 đến 999.999.999.999.')
        return None
    return price


def home_page(request):
    products = active_products()
    search_query = request.GET.get('q', '').strip()

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

    homepage_products = active_products()

    return render(request, 'Product/Home.html', {
        'banner': banner,
        'featured_categories': Category.objects.filter(
            is_active=True,
            is_featured=True,
            parent__isnull=True,
        )[:6],
        'new_products': homepage_products.filter(is_new=True)[:6],
        'best_sellers': homepage_products.filter(is_best_seller=True)[:6],
        'promotion_products': homepage_products.filter(discount_percent__gt=0)[:6],
        'page_obj': page_obj,
        'search_query': search_query,
    })


def category_page(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    category_ids = category_and_children_ids(category)
    products = active_products().filter(category_id__in=category_ids)

    selected_brands = request.GET.getlist('brand')
    selected_sizes = request.GET.getlist('size')
    selected_colors = request.GET.getlist('color')
    selected_gender = request.GET.get('gender', '')
    in_stock = request.GET.get('in_stock') == '1'
    sort = request.GET.get('sort', 'newest')
    min_price_text = request.GET.get('min_price', '').strip()
    max_price_text = request.GET.get('max_price', '').strip()
    errors = []

    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    valid_genders = {value for value, _ in Product.GENDER_CHOICES}
    if selected_gender:
        if selected_gender in valid_genders:
            products = products.filter(gender=selected_gender)
        else:
            errors.append('Giới tính không hợp lệ.')
            selected_gender = ''

    min_price = parse_price(min_price_text, 'Giá thấp nhất', errors)
    max_price = parse_price(max_price_text, 'Giá cao nhất', errors)
    valid_price_range = not (min_price is not None and max_price is not None and min_price > max_price)
    if not valid_price_range:
        errors.append('Giá thấp nhất phải nhỏ hơn hoặc bằng giá cao nhất.')

    variant_filter = Q(variants__is_active=True)
    if selected_sizes:
        variant_filter &= Q(variants__size__in=selected_sizes)
    if selected_colors:
        variant_filter &= Q(variants__color__in=selected_colors)
    if in_stock:
        variant_filter &= Q(variants__stock__gt=0)
    if valid_price_range:
        if min_price is not None:
            variant_filter &= Q(variants__price__gte=min_price)
        if max_price is not None:
            variant_filter &= Q(variants__price__lte=max_price)

    products = products.filter(variant_filter).distinct()

    sort_options = {
        'newest': '-created_at',
        'price_asc': 'variant_min_price',
        'price_desc': '-variant_min_price',
        'popular': '-popularity',
    }
    if sort not in sort_options:
        errors.append('Kiểu sắp xếp không hợp lệ.')
        sort = 'newest'
    products = products.order_by(sort_options[sort], 'id')

    paginator = Paginator(products, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    variant_options = ProductVariant.objects.filter(
        product__category_id__in=category_ids,
        product__is_active=True,
        is_active=True,
    )
    available_sizes = variant_options.values_list('size', flat=True).distinct().order_by('size')
    available_colors = variant_options.values_list('color', flat=True).distinct().order_by('color')
    available_brands = Brand.objects.filter(
        is_active=True,
        products__category_id__in=category_ids,
        products__is_active=True,
    ).distinct()

    breadcrumbs = []
    current = category
    while current:
        breadcrumbs.insert(0, current)
        current = current.parent

    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(request, 'Product/Category.html', {
        'selected_category': category,
        'breadcrumbs': breadcrumbs,
        'category_links': Category.objects.filter(is_active=True, parent=category.parent),
        'available_brands': available_brands,
        'available_sizes': available_sizes,
        'available_colors': available_colors,
        'gender_choices': Product.GENDER_CHOICES,
        'selected_brands': selected_brands,
        'selected_sizes': selected_sizes,
        'selected_colors': selected_colors,
        'selected_gender': selected_gender,
        'min_price': min_price_text,
        'max_price': max_price_text,
        'in_stock': in_stock,
        'sort': sort,
        'filter_errors': errors,
        'page_obj': page_obj,
        'pagination_query': query_params.urlencode(),
    })


def search_page(request):
    search_query = request.GET.get('q', '').strip()
    products = active_products()
    errors = []

    if not search_query:
        products = products.none()
    elif len(search_query) > 80:
        errors.append('Từ khóa tìm kiếm không được vượt quá 80 ký tự.')
        products = products.none()
    else:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(brand__name__icontains=search_query)
            | Q(variants__sku__icontains=search_query)
        ).distinct()

    selected_brands = request.GET.getlist('brand')
    selected_sizes = request.GET.getlist('size')
    selected_colors = request.GET.getlist('color')
    selected_gender = request.GET.get('gender', '')
    in_stock = request.GET.get('in_stock') == '1'
    sort = request.GET.get('sort', 'newest')
    min_price_text = request.GET.get('min_price', '').strip()
    max_price_text = request.GET.get('max_price', '').strip()

    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    valid_genders = {value for value, _ in Product.GENDER_CHOICES}
    if selected_gender:
        if selected_gender in valid_genders:
            products = products.filter(gender=selected_gender)
        else:
            errors.append('Giới tính không hợp lệ.')
            selected_gender = ''

    min_price = parse_price(min_price_text, 'Giá thấp nhất', errors)
    max_price = parse_price(max_price_text, 'Giá cao nhất', errors)
    valid_price_range = not (min_price is not None and max_price is not None and min_price > max_price)
    if not valid_price_range:
        errors.append('Giá thấp nhất phải nhỏ hơn hoặc bằng giá cao nhất.')

    variant_filter = Q(variants__is_active=True)
    if selected_sizes:
        variant_filter &= Q(variants__size__in=selected_sizes)
    if selected_colors:
        variant_filter &= Q(variants__color__in=selected_colors)
    if in_stock:
        variant_filter &= Q(variants__stock__gt=0)
    if valid_price_range:
        if min_price is not None:
            variant_filter &= Q(variants__price__gte=min_price)
        if max_price is not None:
            variant_filter &= Q(variants__price__lte=max_price)
    products = products.filter(variant_filter).distinct()

    sort_options = {
        'newest': '-created_at',
        'price_asc': 'variant_min_price',
        'price_desc': '-variant_min_price',
        'popular': '-popularity',
    }
    if sort not in sort_options:
        errors.append('Kiểu sắp xếp không hợp lệ.')
        sort = 'newest'
    products = products.order_by(sort_options[sort], 'id')

    paginator = Paginator(products, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    variant_options = ProductVariant.objects.filter(product__is_active=True, is_active=True)
    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(request, 'Product/Search.html', {
        'search_query': search_query,
        'page_obj': page_obj,
        'filter_errors': errors,
        'available_brands': Brand.objects.filter(is_active=True, products__is_active=True).distinct(),
        'available_sizes': variant_options.values_list('size', flat=True).distinct().order_by('size'),
        'available_colors': variant_options.values_list('color', flat=True).distinct().order_by('color'),
        'gender_choices': Product.GENDER_CHOICES,
        'selected_brands': selected_brands,
        'selected_sizes': selected_sizes,
        'selected_colors': selected_colors,
        'selected_gender': selected_gender,
        'min_price': min_price_text,
        'max_price': max_price_text,
        'in_stock': in_stock,
        'sort': sort,
        'pagination_query': query_params.urlencode(),
    })


def search_suggest(request):
    now = int(timezone.now().timestamp())
    recent_requests = [
        timestamp
        for timestamp in request.session.get('suggest_requests', [])
        if now - timestamp < 60
    ]
    if len(recent_requests) >= 30:
        return JsonResponse({'results': [], 'error': 'Bạn thao tác quá nhanh.'}, status=429)
    recent_requests.append(now)
    request.session['suggest_requests'] = recent_requests

    search_query = request.GET.get('q', '').strip()
    if len(search_query) < 2 or len(search_query) > 80:
        return JsonResponse({'query': search_query[:80], 'results': []})

    products = active_products().filter(
        Q(name__icontains=search_query)
        | Q(category__name__icontains=search_query)
        | Q(brand__name__icontains=search_query)
        | Q(variants__sku__icontains=search_query)
    ).distinct()[:8]

    results = []
    for product in products:
        results.append({
            'name': product.name,
            'brand': product.brand.name if product.brand else 'QuangHuy',
            'price': int(product.variant_min_price or product.price),
            'image': product.image.url if product.image else '',
            'url': reverse('product_detail', args=[product.slug]),
        })
    return JsonResponse({'query': search_query, 'results': results})


def product_detail(request, product_slug):
    product = get_object_or_404(
        active_products().prefetch_related('images', 'variants'),
        slug=product_slug,
    )
    related_products = active_products().filter(
        category=product.category,
    ).exclude(id=product.id)[:4]

    return render(request, 'Product/Detail.html', {
        'product': product,
        'related_products': related_products,
    })


@require_GET
def product_variants(request, product_slug):
    product = get_object_or_404(active_products(), slug=product_slug)
    variants = product.variants.filter(is_active=True).order_by('size', 'color')
    results = []
    for variant in variants:
        sale_price = variant.price * (100 - product.discount_percent) / 100
        results.append({
            'id': variant.id,
            'sku': variant.sku,
            'size': variant.size,
            'color': variant.color,
            'price': int(variant.price),
            'sale_price': int(sale_price),
            'stock': variant.stock,
            'image': variant.image.url if variant.image else (product.image.url if product.image else ''),
        })
    return JsonResponse({'product': product.name, 'variants': results})


@require_POST
def add_to_cart(request, product_slug):
    from Cart.services import add_variant

    product = get_object_or_404(active_products(), slug=product_slug)
    try:
        variant_id = int(request.POST.get('variant_id', ''))
        quantity = int(request.POST.get('quantity', '1'))
    except (TypeError, ValueError):
        messages.error(request, 'Vui lòng chọn đầy đủ size và màu sắc.')
        return redirect('product_detail', product_slug=product.slug)

    variant = product.variants.filter(id=variant_id, is_active=True).first()
    if variant is None:
        messages.error(request, 'Biến thể đã chọn không hợp lệ.')
        return redirect('product_detail', product_slug=product.slug)
    if quantity < 1:
        messages.error(request, 'Số lượng phải lớn hơn 0.')
        return redirect('product_detail', product_slug=product.slug)

    success, message = add_variant(request, variant, quantity)
    if not success:
        messages.error(request, message)
        return redirect('product_detail', product_slug=product.slug)

    if request.POST.get('action') == 'buy_now':
        request.session['buy_now_variant_id'] = variant.id
        messages.success(request, 'Đã xác nhận sản phẩm. Bước thanh toán sẽ được hoàn thiện ở U08.')
    else:
        messages.success(request, message)
    return redirect('product_detail', product_slug=product.slug)


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
