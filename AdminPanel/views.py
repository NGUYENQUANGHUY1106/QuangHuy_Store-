from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

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

