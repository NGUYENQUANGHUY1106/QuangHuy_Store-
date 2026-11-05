from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from Cart.services import get_cart
from Checkout.models import Order
from Login.models import Address

from .services import shipping_options_for

def shipping_options(request):
    user_id = request.session.get('user_id')
    if not user_id: return JsonResponse({'error':'Vui lòng đăng nhập.'}, status=401)
    address = get_object_or_404(Address, id=request.GET.get('address_id'), user_id=user_id)
    cart = get_cart(request, create=False)
    items = [] if not cart else cart.items.filter(is_selected=True).select_related('variant','variant__product')
    subtotal = sum((item.line_total for item in items), Decimal('0'))
    options = shipping_options_for(address, subtotal)
    return JsonResponse({'options':[{'code':x['code'],'name':x['name'],'fee':int(x['fee']),'eta':f"{x['eta_min']}–{x['eta_max']} ngày"} for x in options]})

def shipment_status(request, order_code):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('login')
    order = get_object_or_404(Order, order_code=order_code, user_id=user_id)
    shipment = getattr(order, 'shipment', None)
    if not shipment: return JsonResponse({'order_code':order_code,'status':'not_created','events':[]})
    return JsonResponse({'order_code':order_code,'carrier':shipment.carrier,'tracking_code':shipment.tracking_code,'tracking_url':shipment.tracking_url,'status':shipment.status,'estimated_delivery':shipment.estimated_delivery,'events':[{'status':e.status,'description':e.description,'occurred_at':e.occurred_at.isoformat()} for e in shipment.events.all()]})
