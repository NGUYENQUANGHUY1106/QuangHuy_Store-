from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Checkout.models import Order
from Login.models import User
from AdminPanel.models import StaffProfile
from Returns.models import Refund,ReturnRequest

from .models import Payment,PaymentTransaction


class PaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='Customer Payment', email='payment@example.com', phone='0912345678',
            password=make_password('secret123'),
        )
        self.order = Order.objects.create(
            user=self.user, order_code='QHPAY001', idempotency_key='pay-key-001',
            payment_method='cod', shipping_method='standard', subtotal=1000000,
            shipping_fee=0, grand_total=1000000,
        )
        self.payment = Payment.objects.create(order=self.order, method='cod', amount=1000000)
        session = self.client.session
        session['user_id'] = self.user.id
        session.save()

    def test_cod_payment_starts_pending_with_correct_amount(self):
        self.assertEqual(self.payment.method, 'cod')
        self.assertEqual(self.payment.status, 'pending')
        self.assertEqual(self.payment.amount, 1000000)

    def test_owner_can_read_payment_status(self):
        response = self.client.get(reverse('payment_status', args=[self.order.order_code]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'pending')
        self.assertEqual(response.json()['amount'], 1000000)

    def test_other_user_cannot_read_payment_status(self):
        other = User.objects.create(
            username='Other Payment', email='other-payment@example.com', phone='0987654321',
            password=make_password('secret123'),
        )
        session = self.client.session
        session['user_id'] = other.id
        session.save()
        response = self.client.get(reverse('payment_status', args=[self.order.order_code]))
        self.assertEqual(response.status_code, 404)


class AdminFinanceTests(TestCase):
    def setUp(self):
        Auth=get_user_model();self.staff=Auth.objects.create_user(username='finance',password='StrongPass123',is_staff=True);StaffProfile.objects.create(user=self.staff,role='FINANCE');self.client.force_login(self.staff)
        self.user=User.objects.create(username='Finance Buyer',email='finance-buyer@example.com',phone='0912345678',password='x')
        self.order=Order.objects.create(user=self.user,order_code='FIN-ORDER',idempotency_key='fin-key',payment_method='cod',shipping_method='standard',subtotal=500000,shipping_fee=0,grand_total=500000)
        self.payment=Payment.objects.create(order=self.order,method='cod',amount=500000)

    def test_cod_only_paid_after_delivery_and_is_idempotent(self):
        url=reverse('finance_admin:mark_cod_paid',args=[self.payment.id]);self.client.post(url);self.payment.refresh_from_db();self.assertEqual(self.payment.status,'pending')
        self.order.status='delivered';self.order.save(update_fields=['status']);self.client.post(url);self.client.post(url);self.payment.refresh_from_db()
        self.assertEqual(self.payment.status,'paid');self.assertEqual(PaymentTransaction.objects.filter(event_id='COD-FIN-ORDER').count(),1)

    def test_amount_mismatch_is_rejected(self):
        self.order.status='delivered';self.order.save(update_fields=['status']);self.payment.amount=400000;self.payment.save(update_fields=['amount'])
        self.client.post(reverse('finance_admin:mark_cod_paid',args=[self.payment.id]));self.payment.refresh_from_db();self.assertEqual(self.payment.status,'pending')

    def test_refund_is_limited_and_idempotent(self):
        self.order.status='completed';self.order.save(update_fields=['status']);self.payment.status='paid';self.payment.save(update_fields=['status'])
        request=ReturnRequest.objects.create(user=self.user,order=self.order,request_type='return',reason='Lỗi',status='approved')
        url=reverse('finance_admin:create_refund',args=[request.id]);self.client.post(url,{'amount':600000,'idempotency_key':'RF-1'});self.assertFalse(Refund.objects.exists())
        self.client.post(url,{'amount':300000,'idempotency_key':'RF-1'});self.client.post(url,{'amount':300000,'idempotency_key':'RF-1'})
        self.assertEqual(Refund.objects.count(),1);self.assertEqual(PaymentTransaction.objects.filter(transaction_type='refund').count(),1)
