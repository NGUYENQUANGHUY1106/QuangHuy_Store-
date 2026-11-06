from functools import wraps

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


ROLE_PERMISSIONS = {
    'PRODUCT': {
        'dashboard.view', 'products.view', 'products.add', 'products.change', 'products.export',
        'categories.view', 'categories.add', 'categories.change',
    },
    'WAREHOUSE': {
        'dashboard.view', 'inventory.view', 'inventory.adjust',
        'suppliers.view', 'suppliers.change',
    },
    'ORDER': {
        'dashboard.view', 'orders.view', 'orders.change', 'shipping.view',
    },
    'SUPPORT': {
        'dashboard.view', 'support.view', 'support.change',
        'reviews.view', 'reviews.change',
    },
    'MARKETING': {
        'dashboard.view', 'marketing.view', 'marketing.change',
        'content.view', 'content.change',
    },
    'FINANCE': {
        'dashboard.view', 'finance.view', 'finance.change', 'finance.export',
        'reports.view', 'reports.export',
    },
}


def get_staff_role(user):
    if not user.is_authenticated or not user.is_staff:
        return None
    try:
        return user.staff_profile.role
    except AttributeError:
        return None


def has_admin_permission(user, permission_code):
    if not user.is_authenticated or not user.is_active or not user.is_staff:
        return False
    if user.is_superuser:
        return True
    role = get_staff_role(user)
    return permission_code in ROLE_PERMISSIONS.get(role, set())


def safe_next_url(request, default_name='admin_panel:dashboard'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse(default_name)


def admin_permission_required(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_url = reverse('admin_panel:login')
                return redirect(f'{login_url}?next={request.get_full_path()}')
            if not has_admin_permission(request.user, permission_code):
                return render(
                    request,
                    'AdminPanel/Forbidden.html',
                    {'required_permission': permission_code},
                    status=403,
                )
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator

