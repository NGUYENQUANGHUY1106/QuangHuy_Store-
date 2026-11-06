from django.contrib import messages
from django.db import IntegrityError,transaction
from django.http import Http404
from django.shortcuts import redirect,render
from django.utils import timezone
from django.views.decorators.http import require_http_methods,require_POST
from AdminPanel.permissions import admin_permission_required
from AdminPanel.services import menu_for_user,write_audit
from Checkout.models import OrderStatusHistory
from Support.models import Notification
from .forms import ShipmentForm,ShippingMethodForm,ShippingZoneForm
from .models import Shipment,ShipmentEvent,ShippingMethod,ShippingZone

def ctx(request,**extra): data={'admin_menu':menu_for_user(request.user)};data.update(extra);return data

@admin_permission_required('shipping.view')
def dashboard(request): return render(request,'Shipping/AdminShipping.html',ctx(request,methods=ShippingMethod.objects.all(),zones=ShippingZone.objects.select_related('method'),shipments=Shipment.objects.select_related('order')))

@admin_permission_required('orders.change')
@require_http_methods(['GET','POST'])
def create_object(request,kind):
    forms={'method':ShippingMethodForm,'zone':ShippingZoneForm,'shipment':ShipmentForm}
    if kind not in forms: raise Http404
    form=forms[kind](request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save();write_audit(request,f'shipping.{kind}.created','Tạo dữ liệu vận chuyển',kind,obj.id);return redirect('shipping_admin:dashboard')
    return render(request,'Shipping/AdminShippingForm.html',ctx(request,form=form,title='Thêm dữ liệu vận chuyển'))

TRANSITIONS={'preparing':['picked'],'picked':['shipping'],'shipping':['delivered','failed'],'failed':['shipping','returned']}

@admin_permission_required('orders.change')
@require_POST
@transaction.atomic
def add_event(request,shipment_id):
    shipment=Shipment.objects.select_for_update().select_related('order').filter(pk=shipment_id).first()
    if not shipment: raise Http404
    event_id=request.POST.get('event_id','').strip();status=request.POST.get('status','');description=request.POST.get('description','').strip()
    if ShipmentEvent.objects.filter(event_id=event_id).exists(): messages.info(request,'Sự kiện này đã được xử lý.');return redirect('shipping_admin:dashboard')
    if status not in TRANSITIONS.get(shipment.status,[]): messages.error(request,'Chuyển trạng thái vận chuyển không hợp lệ.');return redirect('shipping_admin:dashboard')
    ShipmentEvent.objects.create(shipment=shipment,event_id=event_id,status=status,description=description,occurred_at=timezone.now());shipment.status=status;shipment.save(update_fields=['status'])
    if status=='shipping': shipment.order.status='shipping'
    elif status=='delivered': shipment.order.status='delivered'
    shipment.order.save(update_fields=['status']);OrderStatusHistory.objects.create(order=shipment.order,status=shipment.order.status,note=description)
    Notification.objects.create(user=shipment.order.user,title=f'Vận chuyển {shipment.order.order_code}',message=description,link='')
    write_audit(request,'shipment.event',event_id,'shipment',shipment.id);return redirect('shipping_admin:dashboard')
