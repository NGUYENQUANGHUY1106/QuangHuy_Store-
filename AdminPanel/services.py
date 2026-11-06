from .models import AuditLog
from .permissions import has_admin_permission


ADMIN_MENU = [
    {'label': 'Tổng quan', 'permission': 'dashboard.view', 'url_name': 'admin_panel:dashboard'},
    {'label': 'Sản phẩm', 'permission': 'products.view', 'url_name': ''},
    {'label': 'Kho hàng', 'permission': 'inventory.view', 'url_name': ''},
    {'label': 'Đơn hàng', 'permission': 'orders.view', 'url_name': ''},
    {'label': 'Hỗ trợ', 'permission': 'support.view', 'url_name': ''},
    {'label': 'Marketing', 'permission': 'marketing.view', 'url_name': ''},
    {'label': 'Tài chính', 'permission': 'finance.view', 'url_name': ''},
]


def menu_for_user(user):
    return [item for item in ADMIN_MENU if has_admin_permission(user, item['permission'])]


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def write_audit(request, action, description='', target_type='', target_id='', actor=None):
    return AuditLog.objects.create(
        actor=actor if actor is not None else (request.user if request.user.is_authenticated else None),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else '',
        description=description,
        ip_address=client_ip(request),
    )

