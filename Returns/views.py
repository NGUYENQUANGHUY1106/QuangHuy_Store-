from datetime import timedelta
from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from Checkout.models import Order,OrderItem
from Login.models import User
from .models import ReturnEvidence,ReturnItem,ReturnRequest

def current_user(request):
    uid=request.session.get('user_id');return User.objects.filter(id=uid,is_active=True).first() if uid else None

def return_list(request):
    user=current_user(request)
    if not user:return redirect('/login/?next=/account/returns/')
    return render(request,'Returns/ReturnList.html',{'return_requests':user.return_requests.select_related('order')})

def return_create(request,order_code):
    user=current_user(request)
    if not user:return redirect('login')
    order=get_object_or_404(Order.objects.prefetch_related('items'),order_code=order_code,user=user)
    completed_event=order.status_history.filter(status='completed').last()
    completed_at=completed_event.created_at if completed_event else order.created_at
    eligible=order.status=='completed' and completed_at>=timezone.now()-timedelta(days=7)
    if request.method=='POST':
        if not eligible:
            messages.error(request,'Đơn hàng không còn đủ điều kiện đổi/trả.')
            return redirect('order_detail',order_code=order.order_code)
        item=get_object_or_404(OrderItem,id=request.POST.get('order_item_id'),order=order)
        try: quantity=int(request.POST.get('quantity','0'))
        except ValueError: quantity=0
        used=ReturnItem.objects.filter(order_item=item,return_request__status__in=['pending','reviewing','approved','received','refunded','replaced']).aggregate(total=Sum('quantity'))['total'] or 0
        reason=request.POST.get('reason','').strip();kind=request.POST.get('request_type','')
        files=request.FILES.getlist('evidence')
        file_error=any(not getattr(f,'content_type','').startswith('image/') or f.size>2*1024*1024 for f in files) or len(files)>3
        if kind not in {'return','exchange'} or quantity<1 or quantity>item.quantity-used or len(reason)<5 or file_error:
            messages.error(request,'Thông tin đổi/trả, số lượng hoặc ảnh minh chứng không hợp lệ.')
        else:
            result=ReturnRequest.objects.create(user=user,order=order,request_type=kind,reason=reason)
            ReturnItem.objects.create(return_request=result,order_item=item,quantity=quantity)
            for image in files:ReturnEvidence.objects.create(return_request=result,image=image)
            from Support.models import Notification
            Notification.objects.create(user=user,title='Đã nhận yêu cầu đổi/trả',message=f'Yêu cầu #{result.id} đang chờ xử lý.',link=f'/account/returns/{result.id}/')
            messages.success(request,'Đã gửi yêu cầu đổi/trả.')
            return redirect('return_detail',request_id=result.id)
    return render(request,'Returns/ReturnCreate.html',{'order':order,'eligible':eligible})

def return_detail(request,request_id):
    user=current_user(request)
    if not user:return redirect('login')
    result=get_object_or_404(ReturnRequest.objects.select_related('order').prefetch_related('items__order_item','evidence'),id=request_id,user=user)
    return render(request,'Returns/ReturnDetail.html',{'return_request':result})
