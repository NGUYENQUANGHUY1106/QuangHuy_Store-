from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from Cart.models import Cart, CartItem
from Login.models import Address, User
from Product.models import Brand, Category, Product, ProductVariant

from .models import Coupon, CouponUsage, Order, OrderStatusHistory


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='Customer', email='customer@example.com', phone='0912345678',
            password=make_password('secret123'),
        )
        self.address = Address.objects.create(
            user=self.user, recipient_name='Nguyen Van A', phone='0912345678',
            province='Da Nang', ward='Hai Chau', detail='12 Tran Phu', is_default=True,
        )
        brand = Brand.objects.create(name='Nike Checkout', slug='nike-checkout')
        category = Category.objects.create(name='Checkout Test', slug='checkout-test')
        product = Product.objects.create(
            brand=brand, category=category, name='Nike Checkout Test',
            slug='nike-checkout-test', price=1000000, image='products/test.jpg',
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku='CHECK-40', size='40', color='Đen', price=1000000, stock=5,
        )
        self.other_variant = ProductVariant.objects.create(
            product=product, sku='CHECK-41', size='41', color='Trắng', price=500000, stock=5,
        )
        session = self.client.session
        session['user_id'] = self.user.id
        session.save()
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(
            cart=self.cart, variant=self.variant, quantity=2,
            price_when_added=1000000, is_selected=True,
        )

    def checkout_data(self, **changes):
        self.client.get(reverse('checkout'))
        data = {
            'address_id': self.address.id,
            'shipping_method': 'standard',
            'payment_method': 'cod',
            'idempotency_key': self.client.session['checkout_key'],
        }
        data.update(changes)
        return data

    def test_checkout_requires_login(self):
        self.client.session.flush()
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, '/login/?next=/checkout/')

    def test_checkout_page_shows_shipping_fee_and_total_before_submit(self):
        response = self.client.get(reverse('checkout'))

        self.assertEqual(response.context['initial_shipping_fee'], Decimal('0'))
        self.assertEqual(response.context['initial_total'], Decimal('2000000'))
        self.assertContains(response, 'Phí vận chuyển')
        self.assertContains(response, 'checkout-total')
        self.assertContains(response, 'products/test.jpg')

    def test_place_order_snapshots_data_reduces_stock_and_clears_selected_items(self):
        unselected = CartItem.objects.create(
            cart=self.cart, variant=self.other_variant, quantity=1,
            price_when_added=500000, is_selected=False,
        )
        response = self.client.post(reverse('checkout'), self.checkout_data())

        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse('checkout_success', args=[order.order_code]))
        self.assertEqual(order.subtotal, Decimal('2000000'))
        self.assertEqual(order.shipping_fee, 0)
        self.assertEqual(order.grand_total, Decimal('2000000'))
        self.assertEqual(order.items.get().sku, 'CHECK-40')
        self.assertEqual(order.shipping_address.detail, '12 Tran Phu')
        self.variant.refresh_from_db()
        self.address.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertTrue(self.address.is_used_in_order)
        self.assertEqual(order.payment.status, 'pending')
        self.assertEqual(order.payment.amount, order.grand_total)
        self.assertTrue(OrderStatusHistory.objects.filter(order=order, status='pending').exists())
        self.assertFalse(CartItem.objects.filter(id=self.item.id).exists())
        self.assertTrue(CartItem.objects.filter(id=unselected.id).exists())
        detail = self.client.get(reverse('order_detail', args=[order.order_code]))
        self.assertContains(detail, 'products/test.jpg')

    def test_coupon_and_express_shipping_are_calculated_on_server(self):
        coupon = Coupon.objects.create(code='SALE10', discount_percent=10, min_order=100000)
        self.client.post(reverse('checkout'), self.checkout_data(
            coupon_code='sale10', shipping_method='express',
        ))

        order = Order.objects.get(user=self.user)
        self.assertEqual(order.discount, Decimal('200000'))
        self.assertEqual(order.shipping_fee, Decimal('60000'))
        self.assertEqual(order.grand_total, Decimal('1860000'))
        self.assertTrue(CouponUsage.objects.filter(coupon=coupon, order=order).exists())
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)

    def test_expired_and_exhausted_coupon_are_rejected(self):
        expired = Coupon.objects.create(
            code='EXPIRED', discount_percent=10,
            ends_at=timezone.now() - timedelta(minutes=1),
        )
        exhausted = Coupon.objects.create(
            code='FULL', discount_percent=10, usage_limit=1, used_count=1,
        )
        expired_response = self.client.post(reverse('coupon_preview'), {'coupon_code': expired.code})
        full_response = self.client.post(reverse('coupon_preview'), {'coupon_code': exhausted.code})
        self.assertEqual(expired_response.status_code, 400)
        self.assertEqual(full_response.status_code, 400)

    def test_cancel_order_returns_coupon_usage(self):
        coupon = Coupon.objects.create(code='RETURN10', discount_percent=10)
        self.client.post(reverse('checkout'), self.checkout_data(coupon_code=coupon.code))
        order = Order.objects.get(user=self.user)
        self.client.post(reverse('order_cancel', args=[order.order_code]))
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 0)
        self.assertFalse(CouponUsage.objects.filter(order=order).exists())

    def test_repeated_idempotency_key_does_not_create_second_order(self):
        data = self.checkout_data()
        first = self.client.post(reverse('checkout'), data)
        second = self.client.post(reverse('checkout'), data)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(first.url, second.url)

    def test_insufficient_stock_does_not_create_order_or_clear_cart(self):
        self.variant.stock = 1
        self.variant.save(update_fields=['stock'])
        response = self.client.post(reverse('checkout'), self.checkout_data(), follow=True)

        self.assertContains(response, 'không đủ tồn kho')
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(id=self.item.id).exists())

    def test_cannot_use_another_users_address(self):
        other = User.objects.create(
            username='Other', email='other-checkout@example.com', phone='0987654321',
            password=make_password('secret123'),
        )
        other_address = Address.objects.create(
            user=other, recipient_name='Other', phone='0987654321',
            province='Ha Noi', ward='Hoan Kiem', detail='20 Hang Bai',
        )
        response = self.client.post(reverse('checkout'), self.checkout_data(address_id=other_address.id))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Order.objects.exists())

    def place_order(self):
        self.client.post(reverse('checkout'), self.checkout_data())
        return Order.objects.get(user=self.user)

    def test_order_list_and_detail_only_show_owner_orders(self):
        order = self.place_order()
        other = User.objects.create(
            username='Other Order', email='other-order@example.com', phone='0987654321',
            password=make_password('secret123'),
        )
        other_order = Order.objects.create(
            user=other, order_code='QHOTHER001', idempotency_key='other-key',
            payment_method='cod', shipping_method='standard', subtotal=100,
            shipping_fee=0, grand_total=100,
        )

        response = self.client.get(reverse('order_list'))

        self.assertContains(response, order.order_code)
        self.assertNotContains(response, other_order.order_code)
        self.assertEqual(self.client.get(reverse('order_detail', args=[other_order.order_code])).status_code, 404)

    def test_cancel_order_restores_stock_only_once_and_adds_timeline(self):
        order = self.place_order()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)

        self.client.post(reverse('order_cancel', args=[order.order_code]))
        self.client.post(reverse('order_cancel', args=[order.order_code]))

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(self.variant.stock, 5)
        self.assertEqual(OrderStatusHistory.objects.filter(order=order, status='cancelled').count(), 1)

    def test_shipping_order_cannot_be_cancelled(self):
        order = self.place_order()
        order.status = 'shipping'
        order.save(update_fields=['status'])

        self.client.post(reverse('order_cancel', args=[order.order_code]))

        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, 'shipping')
        self.assertEqual(self.variant.stock, 3)

    def test_reorder_adds_available_sku_back_to_cart(self):
        order = self.place_order()
        response = self.client.post(reverse('order_reorder', args=[order.order_code]))

        self.assertRedirects(response, reverse('cart_page'))
        item = CartItem.objects.get(cart=self.cart, variant=self.variant)
        self.assertEqual(item.quantity, 2)
