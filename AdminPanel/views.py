from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import csv

from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from Product.models import Brand, Category, Product, ProductImage, SportType

from .forms import BrandForm, CategoryForm, ProductForm, SportTypeForm
from .permissions import admin_permission_required, get_staff_role, has_admin_permission, safe_next_url
from .services import dashboard_data, menu_for_user, write_audit


def page_context(request, **extra):
    context = {
        'admin_menu': menu_for_user(request.user),
        'staff_role': get_staff_role(request.user),
    }
    context.update(extra)
    return context


@require_http_methods(['GET', 'POST'])
def admin_login(request):
    if has_admin_permission(request.user, 'dashboard.view'):
        return redirect('admin_panel:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        now = int(timezone.now().timestamp())
        attempts = [item for item in request.session.get('admin_login_attempts', []) if now - item < 300]

        if len(attempts) >= 10:
            return render(request, 'AdminPanel/Login.html', {
                'error': 'Bạn đã thử quá nhiều lần. Vui lòng đợi 5 phút.',
                'username': username,
                'next': request.POST.get('next', ''),
            }, status=429)

        user = authenticate(request, username=username, password=password)
        allowed = user and has_admin_permission(user, 'dashboard.view')
        if not allowed:
            attempts.append(now)
            request.session['admin_login_attempts'] = attempts
            write_audit(request, 'admin.login_failed', 'Đăng nhập Admin không thành công.')
            return render(request, 'AdminPanel/Login.html', {
                'error': 'Tài khoản, mật khẩu hoặc quyền nhân viên không hợp lệ.',
                'username': username,
                'next': request.POST.get('next', ''),
            })

        login(request, user)
        request.session.pop('admin_login_attempts', None)
        request.session.set_expiry(8 * 60 * 60)
        write_audit(request, 'admin.login', 'Nhân viên đăng nhập.', actor=user)
        return redirect(safe_next_url(request))

    return render(request, 'AdminPanel/Login.html', {'next': request.GET.get('next', '')})


@require_POST
def admin_logout(request):
    if request.user.is_authenticated:
        write_audit(request, 'admin.logout', 'Nhân viên đăng xuất.')
    logout(request)
    return redirect('admin_panel:login')


@admin_permission_required('dashboard.view')
def dashboard(request):
    try:
        data = dashboard_data(request.GET.get('from', ''), request.GET.get('to', ''))
    except ValueError as error:
        data = dashboard_data()
        data['filter_error'] = str(error)
    data['can_view_finance'] = has_admin_permission(request.user, 'finance.view')
    data['can_view_orders'] = has_admin_permission(request.user, 'orders.view')
    data['can_view_inventory'] = (
        has_admin_permission(request.user, 'inventory.view')
        or has_admin_permission(request.user, 'products.view')
    )
    return render(request, 'AdminPanel/Dashboard.html', page_context(request, **data))


@admin_permission_required('dashboard.view')
def admin_me(request):
    return JsonResponse({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'role': get_staff_role(request.user) or 'SUPERUSER',
        'is_superuser': request.user.is_superuser,
    })


@admin_permission_required('dashboard.view')
@require_http_methods(['GET', 'POST'])
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        write_audit(request, 'admin.password_changed', 'Nhân viên đổi mật khẩu.')
        messages.success(request, 'Đổi mật khẩu thành công.')
        return redirect('admin_panel:change_password')
    return render(request, 'AdminPanel/ChangePassword.html', page_context(request, form=form))


@admin_permission_required('staff.manage_permissions')
def permission_test(request):
    return JsonResponse({'allowed': True})


def forbidden(request):
    return render(request, 'AdminPanel/Forbidden.html', status=403)


CATALOGS = {
    'category': (Category, CategoryForm, 'Danh mục', 'admin_panel:categories'),
    'brand': (Brand, BrandForm, 'Thương hiệu', 'admin_panel:brands'),
    'sport': (SportType, SportTypeForm, 'Môn thể thao', 'admin_panel:sports'),
}


def get_catalog(kind):
    if kind not in CATALOGS:
        raise Http404
    return CATALOGS[kind]


def catalog_list(request, kind):
    model, form_class, title, list_url = get_catalog(kind)
    keyword = request.GET.get('q', '').strip()
    objects = model.objects.all()
    if keyword:
        objects = objects.filter(name__icontains=keyword)
    return render(request, 'AdminPanel/CatalogList.html', page_context(
        request, objects=objects, kind=kind, page_title=title, keyword=keyword,
        can_add=has_admin_permission(request.user, 'categories.add'),
        can_change=has_admin_permission(request.user, 'categories.change'),
    ))


@admin_permission_required('categories.view')
def categories(request): return catalog_list(request, 'category')


@admin_permission_required('categories.view')
def brands(request): return catalog_list(request, 'brand')


@admin_permission_required('categories.view')
def sports(request): return catalog_list(request, 'sport')


@admin_permission_required('categories.add')
@require_http_methods(['GET', 'POST'])
def catalog_create(request, kind):
    model, form_class, title, list_url = get_catalog(kind)
    form = form_class(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        write_audit(request, f'catalog.{kind}.created', f'Tạo {title}: {obj.name}', kind, obj.id)
        messages.success(request, f'Đã tạo {title.lower()}.')
        return redirect(list_url)
    return render(request, 'AdminPanel/CatalogForm.html', page_context(request, form=form, page_title=f'Thêm {title.lower()}', back_url=reverse(list_url)))


@admin_permission_required('categories.change')
@require_http_methods(['GET', 'POST'])
def catalog_edit(request, kind, object_id):
    model, form_class, title, list_url = get_catalog(kind)
    obj = model.objects.filter(pk=object_id).first()
    if not obj: raise Http404
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        write_audit(request, f'catalog.{kind}.updated', f'Sửa {title}: {obj.name}', kind, obj.id)
        messages.success(request, f'Đã cập nhật {title.lower()}.')
        return redirect(list_url)
    return render(request, 'AdminPanel/CatalogForm.html', page_context(request, form=form, page_title=f'Sửa {title.lower()}', back_url=reverse(list_url)))


@admin_permission_required('categories.change')
@require_POST
def catalog_toggle(request, kind, object_id):
    model, form_class, title, list_url = get_catalog(kind)
    obj = model.objects.filter(pk=object_id).first()
    if not obj: raise Http404
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    write_audit(request, f'catalog.{kind}.visibility', f'Đổi trạng thái {obj.name}', kind, obj.id)
    return redirect(list_url)


@admin_permission_required('products.view')
def products(request):
    items = Product.objects.select_related('category', 'brand')
    keyword = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if keyword:
        items = items.filter(Q(name__icontains=keyword) | Q(variants__sku__icontains=keyword)).distinct()
    if status in dict(Product.STATUS_CHOICES):
        items = items.filter(status=status)
    return render(request, 'AdminPanel/ProductList.html', page_context(
        request, products=items, keyword=keyword, selected_status=status,
        status_choices=Product.STATUS_CHOICES,
        can_change=has_admin_permission(request.user, 'products.change'),
    ))


@admin_permission_required('products.add')
@require_http_methods(['GET', 'POST'])
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save(commit=False)
        product.status = 'draft'; product.is_active = False
        product.save()
        write_audit(request, 'product.created', f'Tạo bản nháp {product.name}', 'product', product.id)
        return redirect('admin_panel:product_edit', product.id)
    return render(request, 'AdminPanel/ProductForm.html', page_context(request, form=form, page_title='Thêm sản phẩm', product=None))


@admin_permission_required('products.change')
@require_http_methods(['GET', 'POST'])
def product_edit(request, product_id):
    product = Product.objects.filter(pk=product_id).first()
    if not product: raise Http404
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        write_audit(request, 'product.updated', f'Sửa {product.name}', 'product', product.id)
        messages.success(request, 'Đã cập nhật sản phẩm.')
        return redirect('admin_panel:product_edit', product.id)
    return render(request, 'AdminPanel/ProductForm.html', page_context(request, form=form, page_title='Sửa sản phẩm', product=product))


@admin_permission_required('products.change')
@require_POST
def product_publish(request, product_id):
    product = Product.objects.filter(pk=product_id).first()
    if not product: raise Http404
    if not product.variants.filter(is_active=True).exists():
        messages.error(request, 'Cần ít nhất một SKU đang hoạt động trước khi công bố.')
        return redirect('admin_panel:product_edit', product.id)
    product.status = 'published'; product.is_active = True
    product.save(update_fields=['status', 'is_active'])
    write_audit(request, 'product.published', f'Công bố {product.name}', 'product', product.id)
    return redirect('admin_panel:product_edit', product.id)


@admin_permission_required('products.change')
@require_POST
def product_archive(request, product_id):
    product = Product.objects.filter(pk=product_id).first()
    if not product: raise Http404
    product.status = 'archived'; product.is_active = False
    product.save(update_fields=['status', 'is_active'])
    write_audit(request, 'product.archived', f'Ẩn {product.name}', 'product', product.id)
    return redirect('admin_panel:products')


@admin_permission_required('products.change')
@require_POST
def product_bulk_hide(request):
    ids = request.POST.getlist('product_ids')
    Product.objects.filter(id__in=ids).update(status='archived', is_active=False)
    write_audit(request, 'product.bulk_archived', f'Ẩn {len(ids)} sản phẩm')
    return redirect('admin_panel:products')


@admin_permission_required('products.change')
@require_POST
def product_image_add(request, product_id):
    product = Product.objects.filter(pk=product_id).first()
    if not product: raise Http404
    image = request.FILES.get('image')
    if not image or not getattr(image, 'content_type', '').startswith('image/') or image.size > 5 * 1024 * 1024:
        messages.error(request, 'Ảnh phải đúng định dạng và không quá 5 MB.')
    else:
        ProductImage.objects.create(product=product, image=image, alt_text=request.POST.get('alt_text', '')[:200])
        write_audit(request, 'product.image_added', f'Thêm ảnh {product.name}', 'product', product.id)
    return redirect('admin_panel:product_edit', product.id)


@admin_permission_required('products.change')
@require_POST
def product_image_delete(request, image_id):
    image = ProductImage.objects.filter(pk=image_id).first()
    if not image: raise Http404
    product_id = image.product_id
    image.delete()
    write_audit(request, 'product.image_deleted', 'Xóa ảnh phụ', 'product', product_id)
    return redirect('admin_panel:product_edit', product_id)


@admin_permission_required('products.export')
def product_export(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    response.write('\ufeff')
    writer = csv.writer(response); writer.writerow(['Tên','Slug','Danh mục','Thương hiệu','Giá','Trạng thái'])
    for item in Product.objects.select_related('category','brand'):
        writer.writerow([item.name,item.slug,item.category.name,item.brand.name if item.brand else '',item.price,item.status])
    write_audit(request, 'product.exported', 'Xuất danh sách sản phẩm')
    return response

