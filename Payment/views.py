from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect

from Checkout.models import Order


def payment_status(request, order_code):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    order = get_object_or_404(Order.objects.select_related('payment'), order_code=order_code, user_id=user_id)
    return JsonResponse({
        'order_code': order.order_code,
        'method': order.payment.method,
        'status': order.payment.status,
        'amount': int(order.payment.amount),
    })
