from decimal import Decimal,InvalidOperation
from django.contrib import messages
from django.db import models,transaction
from django.http import Http404
from django.shortcuts import redirect,render
from django.utils import timezone
from django.views.decorators.http import require_POST
from AdminPanel.permissions import admin_permission_required
from AdminPanel.services import menu_for_user,write_audit
from Returns.models import Refund,ReturnRequest
from .models import Payment,PaymentTransaction

def ctx(request,**extra): data={'admin_menu':menu_for_user(request.user)};data.update(extra);return data

@admin_permission_required('finance.view')
def dashboard(request):
    payments=Payment.objects.select_related('order','order__user').prefetch_related('transactions')
    status=request.GET.get('status','')
    if status: payments=payments.filter(status=status)
    return render(request,'Payment/AdminFinance.html',ctx(request,payments=payments,refunds=Refund.objects.select_related('return_request__order'),selected_status=status))

@admin_permission_required('finance.change')
@require_POST
@transaction.atomic
def mark_cod_paid(request,payment_id):
    payment=Payment.objects.select_for_update().select_related('order').filter(pk=payment_id,method='cod').first()
    if not payment: raise Http404
    if payment.status=='paid': messages.info(request,'Khoản COD đã được ghi nhận trước đó.');return redirect('finance_admin:dashboard')
    delivered=payment.order.status in ['delivered','completed']
    if not delivered: messages.error(request,'Chỉ ghi nhận COD sau khi giao hàng thành công.');return redirect('finance_admin:dashboard')
    if payment.amount!=payment.order.grand_total: messages.error(request,'Số tiền payment không khớp đơn hàng.');return redirect('finance_admin:dashboard')
    payment.status='paid';payment.paid_at=timezone.now();payment.save(update_fields=['status','paid_at','updated_at'])
    PaymentTransaction.objects.get_or_create(event_id=f'COD-{payment.order.order_code}',defaults={'payment':payment,'status':'success','amount':payment.amount,'provider_ref':payment.order.order_code})
    write_audit(request,'payment.cod_paid',payment.order.order_code,'payment',payment.id);return redirect('finance_admin:dashboard')

@admin_permission_required('finance.change')
@require_POST
@transaction.atomic
def create_refund(request,return_id):
    key=request.POST.get('idempotency_key','').strip()
    if not key: messages.error(request,'Cần mã xử lý duy nhất.');return redirect('finance_admin:dashboard')
    existing=Refund.objects.filter(idempotency_key=key).first()
    if existing: messages.info(request,'Yêu cầu hoàn tiền đã được xử lý.');return redirect('finance_admin:dashboard')
    return_request=ReturnRequest.objects.select_for_update().select_related('order').filter(pk=return_id,status__in=['approved','received']).first()
    if not return_request: raise Http404
    payment=Payment.objects.select_for_update().get(order=return_request.order)
    try: amount=Decimal(request.POST.get('amount','0'))
    except InvalidOperation: amount=Decimal('-1')
    refunded=Refund.objects.filter(return_request__order=return_request.order,status='completed').exclude(return_request=return_request).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    if amount<=0 or amount>payment.amount-refunded: messages.error(request,'Số tiền hoàn không hợp lệ.');return redirect('finance_admin:dashboard')
    refund=Refund.objects.create(return_request=return_request,amount=amount,status='completed',idempotency_key=key,processed_at=timezone.now())
    PaymentTransaction.objects.create(payment=payment,event_id=f'REFUND-{key}',provider_ref=str(refund.id),transaction_type='refund',status='success',amount=amount)
    return_request.status='refunded';return_request.save(update_fields=['status']);write_audit(request,'payment.refunded',key,'refund',refund.id);return redirect('finance_admin:dashboard')
