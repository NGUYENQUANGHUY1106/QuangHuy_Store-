from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from Cart.models import Cart, CartItem
from Login.models import Address, User
from Product.models import Brand, Category, Product, ProductVariant

from .models import Coupon, CouponUsage, Order


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
        self.assertFalse(CartItem.objects.filter(id=self.item.id).exists())
        self.assertTrue(CartItem.objects.filter(id=unselected.id).exists())

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
