from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from Checkout.models import Order
from Login.models import User as Customer
from Payment.models import Payment
from Product.models import ProductVariant

from .models import AuditLog
from .permissions import has_admin_permission


ADMIN_MENU = [
    {'label': 'Tổng quan', 'permission': 'dashboard.view', 'url_name': 'admin_panel:dashboard'},
    {'label': 'Danh mục', 'permission': 'categories.view', 'url_name': 'admin_panel:categories'},
    {'label': 'Sản phẩm', 'permission': 'products.view', 'url_name': 'admin_panel:products'},
    {'label': 'Kho hàng', 'permission': 'inventory.view', 'url_name': 'inventory:stock_list'},
    {'label': 'Nhập hàng', 'permission': 'suppliers.view', 'url_name': 'inventory:procurement'},
    {'label': 'Đơn hàng', 'permission': 'orders.view', 'url_name': 'admin_panel:orders'},
    {'label': 'Vận chuyển', 'permission': 'shipping.view', 'url_name': 'shipping_admin:dashboard'},
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


def dashboard_period(from_value='', to_value=''):
    vietnam_tz = ZoneInfo('Asia/Ho_Chi_Minh')
    today = timezone.now().astimezone(vietnam_tz).date()
    try:
        from_date = datetime.strptime(from_value, '%Y-%m-%d').date() if from_value else today - timedelta(days=29)
        to_date = datetime.strptime(to_value, '%Y-%m-%d').date() if to_value else today
    except ValueError as error:
        raise ValueError('Ngày lọc phải có định dạng YYYY-MM-DD.') from error
    if from_date > to_date:
        raise ValueError('Ngày bắt đầu không được lớn hơn ngày kết thúc.')
    if (to_date - from_date).days > 365:
        raise ValueError('Mỗi lần chỉ xem tối đa 366 ngày.')
    start = timezone.make_aware(datetime.combine(from_date, time.min), vietnam_tz)
    end = timezone.make_aware(datetime.combine(to_date + timedelta(days=1), time.min), vietnam_tz)
    return from_date, to_date, start, end, vietnam_tz


def dashboard_data(from_value='', to_value=''):
    from_date, to_date, start, end, vietnam_tz = dashboard_period(from_value, to_value)
    orders = Order.objects.filter(created_at__gte=start, created_at__lt=end)
    paid_payments = Payment.objects.filter(
        status='paid',
        paid_at__gte=start,
        paid_at__lt=end,
    ).exclude(order__status='cancelled')

    order_rows = list(
        orders.annotate(day=TruncDate('created_at', tzinfo=vietnam_tz))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )
    maximum = max([row['total'] for row in order_rows], default=1)
    order_chart = [
        {
            'day': row['day'],
            'total': row['total'],
            'percent': max(8, round(row['total'] * 100 / maximum)),
        }
        for row in order_rows
    ]

    return {
        'from_date': from_date,
        'to_date': to_date,
        'orders_total': orders.count(),
        'orders_pending': orders.filter(status='pending').count(),
        'orders_completed': orders.filter(status='completed').count(),
        'orders_cancelled': orders.filter(status='cancelled').count(),
        'revenue': paid_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
        'customers_total': Customer.objects.count(),
        'low_stock_count': ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True,
            stock__lte=5,
        ).count(),
        'low_stock_variants': ProductVariant.objects.filter(
            is_active=True,
            product__is_active=True,
            stock__lte=5,
        ).select_related('product').order_by('stock', 'sku')[:8],
        'recent_orders': orders.select_related('user').order_by('-created_at')[:8],
        'order_chart': order_chart,
    }

