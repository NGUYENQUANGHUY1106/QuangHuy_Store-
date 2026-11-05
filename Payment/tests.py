from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from Checkout.models import Order
from Login.models import User

from .models import Payment


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
