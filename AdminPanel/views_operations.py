import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from Checkout.models import Coupon, Order, OrderItem, Promotion
from Inventory.models import Stock, StockMovement, Warehouse
from Login.models import User as Customer
from Payment.models import Payment
from Product.models import Banner, ProductVariant
from Returns.models import Refund, ReturnEvent, ReturnRequest
from Reviews.models import Review
from Support.models import (BlogPost, FAQ, Notification, SiteSettings, StaticPage,
                            SupportMessage, SupportTicket)

from .forms_operations import (BannerForm, BlogPostForm, CouponForm, FAQForm,
                               PromotionForm, SiteSettingsForm, StaffForm,
                               StaticPageForm)
from .models import AuditLog, StaffProfile
from .permissions import admin_permission_required
from .services import menu_for_user, write_audit


def context(request, **extra):
    data = {'admin_menu': menu_for_user(request.user)}
    data.update(extra)
    return data


# A11 - đổi trả
@admin_permission_required('returns.view')
def returns_list(request):
    items = ReturnRequest.objects.select_related('user', 'order').prefetch_related('items')
    status = request.GET.get('status', '')
    if status:
        items = items.filter(status=status)
    return render(request, 'AdminPanel/Returns.html', context(request, returns=items,
                  status_choices=ReturnRequest.STATUS_CHOICES, selected_status=status))


@admin_permission_required('returns.view')
def return_detail(request, return_id):
    item = ReturnRequest.objects.select_related('user', 'order', 'exchange_variant').prefetch_related(
        'items__order_item__variant', 'evidence', 'events').filter(pk=return_id).first()
    if not item:
        raise Http404
    variants = ProductVariant.objects.filter(is_active=True, stock__gt=0).select_related('product')
    return render(request, 'AdminPanel/ReturnDetail.html', context(request, item=item, variants=variants,
                  warehouses=Warehouse.objects.filter(is_active=True)))


def set_return_status(request, item, status, note):
    item.status = status
    item.admin_note = note
    item.save(update_fields=['status', 'admin_note'])
    ReturnEvent.objects.create(return_request=item, status=status, note=note, actor=request.user)
    Notification.objects.create(user=item.user, title=f'Yêu cầu đổi trả #{item.id}',
                                message=f'Trạng thái mới: {item.get_status_display()}',
                                link=reverse('return_detail', args=[item.id]))
    write_audit(request, f'return.{status}', note, 'return', item.id)


@admin_permission_required('returns.change')
@require_POST
@transaction.atomic
def return_action(request, return_id, action):
    item = ReturnRequest.objects.select_for_update().filter(pk=return_id).first()
    if not item:
        raise Http404
    note = request.POST.get('note', '').strip()
    if action == 'approve' and item.status in ['pending', 'reviewing']:
        set_return_status(request, item, 'approved', note)
    elif action == 'reject' and item.status in ['pending', 'reviewing'] and note:
        set_return_status(request, item, 'rejected', note)
    elif action == 'receive' and item.status == 'approved':
        warehouse = Warehouse.objects.filter(pk=request.POST.get('warehouse_id'), is_active=True).first()
        if not warehouse:
            messages.error(request, 'Hãy chọn kho nhận hàng.')
            return redirect('admin_panel:return_detail', item.id)
        for returned in item.items.select_related('order_item__variant'):
            if returned.restocked:
                continue
            try:
                quantity = int(request.POST.get(f'quantity_{returned.id}', returned.quantity))
            except ValueError:
                quantity = 0
            quantity = max(0, min(returned.quantity, quantity))
            returned.received_quantity = quantity
            returned.condition = request.POST.get(f'condition_{returned.id}', '')[:100]
            if request.POST.get(f'restock_{returned.id}') == 'on' and quantity:
                stock, _ = Stock.objects.select_for_update().get_or_create(
                    warehouse=warehouse, variant=returned.order_item.variant)
                before = stock.on_hand
                stock.on_hand += quantity
                stock.save(update_fields=['on_hand', 'updated_at'])
                StockMovement.objects.create(stock=stock, movement_type='return', quantity=quantity,
                    before_quantity=before, after_quantity=stock.on_hand,
                    reason=f'Nhận hàng hoàn #{item.id}', actor=request.user, reference=f'RETURN-{item.id}')
                returned.restocked = True
            returned.save(update_fields=['received_quantity', 'condition', 'restocked'])
            returned.order_item.variant.stock = sum(
                row.available for row in Stock.objects.filter(
                    variant=returned.order_item.variant,
                    warehouse__is_online=True,
                    warehouse__is_active=True,
                )
            )
            returned.order_item.variant.save(update_fields=['stock'])
        item.received_at = timezone.now()
        item.save(update_fields=['received_at'])
        set_return_status(request, item, 'received', note)
    elif action == 'replace' and item.status == 'received':
        variant = ProductVariant.objects.filter(pk=request.POST.get('exchange_variant_id'), is_active=True).first()
        quantity = sum(x.received_quantity for x in item.items.all())
        stock = Stock.objects.select_for_update().filter(
            warehouse_id=request.POST.get('warehouse_id'), variant=variant).first()
        if not variant or not stock or stock.available < quantity:
            messages.error(request, 'SKU đổi không hợp lệ hoặc không đủ tồn.')
            return redirect('admin_panel:return_detail', item.id)
        before = stock.on_hand
        stock.on_hand -= quantity
        stock.save(update_fields=['on_hand', 'updated_at'])
        StockMovement.objects.create(stock=stock, movement_type='sale', quantity=-quantity,
            before_quantity=before, after_quantity=stock.on_hand,
            reason=f'Cấp SKU đổi cho yêu cầu #{item.id}', actor=request.user,
            reference=f'EXCHANGE-{item.id}')
        variant.stock = sum(row.available for row in Stock.objects.filter(
            variant=variant, warehouse__is_online=True, warehouse__is_active=True))
        variant.save(update_fields=['stock'])
        item.exchange_variant = variant
        item.save(update_fields=['exchange_variant'])
        set_return_status(request, item, 'replaced', note)
    else:
        messages.error(request, 'Thao tác không hợp lệ hoặc thiếu lý do.')
    return redirect('admin_panel:return_detail', item.id)


# A12 - khách hàng và nhân viên
@admin_permission_required('customers.view')
def customers(request):
    keyword = request.GET.get('q', '').strip()
    items = Customer.objects.annotate(order_count=Count('orders'))
    if keyword:
        items = items.filter(Q(email__icontains=keyword) | Q(username__icontains=keyword) | Q(phone__icontains=keyword))
    return render(request, 'AdminPanel/Customers.html', context(request, customers=items, keyword=keyword))


@admin_permission_required('customers.change')
@require_POST
def customer_toggle(request, customer_id):
    customer = Customer.objects.filter(pk=customer_id).first()
    if not customer:
        raise Http404
    customer.is_active = not customer.is_active
    customer.locked_reason = request.POST.get('reason', '')[:255] if not customer.is_active else ''
    customer.save(update_fields=['is_active', 'locked_reason'])
    write_audit(request, 'customer.lock_changed', customer.locked_reason, 'customer', customer.id)
    return redirect('admin_panel:customers')


@admin_permission_required('staff.view')
def staff_list(request):
    users = get_user_model().objects.filter(is_staff=True).select_related('staff_profile')
    return render(request, 'AdminPanel/StaffList.html', context(request, staff_users=users))


@admin_permission_required('staff.change')
@require_http_methods(['GET', 'POST'])
def staff_form(request, user_id=None):
    user = get_user_model().objects.filter(pk=user_id, is_staff=True).first() if user_id else None
    if user_id and not user:
        raise Http404
    form = StaffForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        if not user:
            if not form.cleaned_data['password']:
                form.add_error('password', 'Cần nhập mật khẩu khi tạo nhân viên.')
                return render(request, 'AdminPanel/OperationForm.html', context(request, form=form, title='Nhân viên'))
            user = get_user_model().objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
        user.username = form.cleaned_data['username']; user.email = form.cleaned_data['email']
        user.is_staff = True; user.is_active = form.cleaned_data['is_active']
        if form.cleaned_data['password']:
            user.set_password(form.cleaned_data['password'])
        user.save()
        StaffProfile.objects.update_or_create(user=user, defaults={'role': form.cleaned_data['role']})
        write_audit(request, 'staff.saved', f'{user.username} - {form.cleaned_data["role"]}', 'staff', user.id)
        return redirect('admin_panel:staff')
    return render(request, 'AdminPanel/OperationForm.html', context(request, form=form, title='Nhân viên'))


# A13/A14 - marketing và nội dung
CRUD = {
    'coupon': (Coupon, CouponForm, 'Mã giảm giá', 'marketing.change'),
    'promotion': (Promotion, PromotionForm, 'Chương trình khuyến mãi', 'marketing.change'),
    'banner': (Banner, BannerForm, 'Banner', 'content.change'),
    'blog': (BlogPost, BlogPostForm, 'Bài viết', 'content.change'),
    'faq': (FAQ, FAQForm, 'FAQ', 'content.change'),
    'page': (StaticPage, StaticPageForm, 'Trang chính sách', 'content.change'),
}


@admin_permission_required('marketing.view')
def marketing(request):
    return render(request, 'AdminPanel/Marketing.html', context(request,
        coupons=Coupon.objects.all(), promotions=Promotion.objects.all()))


@admin_permission_required('content.view')
def content(request):
    return render(request, 'AdminPanel/Content.html', context(request, banners=Banner.objects.all(),
        blogs=BlogPost.objects.all(), faqs=FAQ.objects.all(), pages=StaticPage.objects.all()))


@require_http_methods(['GET', 'POST'])
def crud_form(request, kind, object_id=None):
    if kind not in CRUD:
        raise Http404
    model, form_class, title, permission = CRUD[kind]
    # Decorator động để cùng một form đơn giản vẫn kiểm quyền đúng.
    from .permissions import has_admin_permission
    if not has_admin_permission(request.user, permission):
        return render(request, 'AdminPanel/Forbidden.html', {'required_permission': permission}, status=403)
    obj = model.objects.filter(pk=object_id).first() if object_id else None
    if object_id and not obj:
        raise Http404
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        write_audit(request, f'{kind}.saved', str(obj), kind, obj.id)
        return redirect('admin_panel:marketing' if kind in ['coupon', 'promotion'] else 'admin_panel:content')
    return render(request, 'AdminPanel/OperationForm.html', context(request, form=form, title=title))


# A15 - đánh giá, ticket
@admin_permission_required('support.view')
def support_queue(request):
    reviews = Review.objects.select_related('user', 'product').prefetch_related('reports')
    tickets = SupportTicket.objects.select_related('user', 'assigned_to').prefetch_related('messages')
    return render(request, 'AdminPanel/SupportQueue.html', context(request, reviews=reviews, tickets=tickets))


@admin_permission_required('reviews.change')
@require_POST
def review_moderate(request, review_id):
    review = Review.objects.filter(pk=review_id).first()
    status = request.POST.get('status')
    if not review or status not in dict(Review.STATUS_CHOICES):
        raise Http404
    review.status = status; review.save(update_fields=['status', 'updated_at'])
    write_audit(request, 'review.moderated', request.POST.get('reason', '')[:500], 'review', review.id)
    return redirect('admin_panel:support')


@admin_permission_required('support.change')
@require_POST
def ticket_action(request, ticket_id):
    ticket = SupportTicket.objects.filter(pk=ticket_id).first()
    if not ticket:
        raise Http404
    action = request.POST.get('action')
    if action == 'reply' and request.POST.get('message', '').strip():
        SupportMessage.objects.create(ticket=ticket, message=request.POST['message'].strip(), is_staff_reply=True)
        ticket.status = 'answered'; ticket.assigned_to = request.user
        Notification.objects.create(user=ticket.user, title=f'Ticket #{ticket.id} có phản hồi',
                                    message=request.POST['message'].strip()[:500],
                                    link=reverse('ticket_detail', args=[ticket.id]))
    elif action in ['open', 'closed']:
        ticket.status = action
    else:
        messages.error(request, 'Thao tác ticket không hợp lệ.')
        return redirect('admin_panel:support')
    ticket.save(update_fields=['status', 'assigned_to'])
    write_audit(request, 'ticket.updated', action, 'ticket', ticket.id)
    return redirect('admin_panel:support')


# A16 - báo cáo
def report_rows(from_date=None, to_date=None):
    orders = Order.objects.exclude(status='cancelled')
    if from_date:
        orders = orders.filter(created_at__date__gte=from_date)
    if to_date:
        orders = orders.filter(created_at__date__lte=to_date)
    paid = Payment.objects.filter(order__in=orders, status='paid')
    refunds = Refund.objects.filter(return_request__order__in=orders, status='completed')
    products = OrderItem.objects.filter(order__in=orders).values('sku', 'product_name').annotate(
        quantity=Sum('quantity'), revenue=Sum('line_total')).order_by('-quantity')[:20]
    return orders, paid, refunds, products


@admin_permission_required('reports.view')
def reports(request):
    orders, paid, refunds, products = report_rows(request.GET.get('from'), request.GET.get('to'))
    return render(request, 'AdminPanel/Reports.html', context(request, products=products,
        order_count=orders.count(), revenue=paid.aggregate(v=Sum('amount'))['v'] or Decimal('0'),
        refunds=refunds.aggregate(v=Sum('amount'))['v'] or Decimal('0'),
        low_stock=Stock.objects.filter(on_hand__lte=5).select_related('variant')[:20]))


@admin_permission_required('reports.export')
def reports_export(request):
    orders, paid, refunds, products = report_rows(request.GET.get('from'), request.GET.get('to'))
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="sales-report.csv"'; response.write('\ufeff')
    writer = csv.writer(response); writer.writerow(['Mã đơn', 'Trạng thái', 'Tổng tiền', 'Ngày tạo'])
    for order in orders:
        writer.writerow([order.order_code, order.get_status_display(), order.grand_total, order.created_at])
    write_audit(request, 'reports.exported', f'{orders.count()} orders')
    return response


# A17 - cấu hình, nhật ký
@admin_permission_required('settings.view')
@require_http_methods(['GET', 'POST'])
def settings_page(request):
    item = SiteSettings.objects.first() or SiteSettings.objects.create()
    field_names = list(SiteSettingsForm.Meta.fields)
    before_snapshot = {name: str(getattr(item, name)) for name in field_names}
    form = SiteSettingsForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False); item.version += 1; item.save()
        log = write_audit(request, 'settings.updated', f'Phiên bản {item.version}', 'settings', item.id)
        log.before_data = before_snapshot
        log.after_data = {name: str(getattr(item, name)) for name in field_names}
        log.save(update_fields=['before_data', 'after_data'])
        messages.success(request, 'Đã lưu cấu hình hệ thống.')
        return redirect('admin_panel:settings')
    return render(request, 'AdminPanel/Settings.html', context(request, form=form, item=item))


@admin_permission_required('audit.view')
def audit_logs(request):
    logs = AuditLog.objects.select_related('actor')
    action = request.GET.get('action', '').strip()
    if action:
        logs = logs.filter(action__icontains=action)
    return render(request, 'AdminPanel/AuditLogs.html', context(request, logs=logs[:500], action=action))
