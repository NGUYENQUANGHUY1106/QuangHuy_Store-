from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from Login.models import User
from Product.models import Brand, Category, Product, ProductVariant

from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name='Nike', slug='nike-cart')
        category = Category.objects.create(name='Giày test cart', slug='giay-test-cart')
        self.product = Product.objects.create(
            brand=brand, category=category, name='Nike Mercurial Test',
            slug='nike-mercurial-test', price=3000000, image='products/test.jpg',
        )
        self.variant_40 = ProductVariant.objects.create(
            product=self.product, sku='TEST-40', size='40', color='Đen', price=3000000, stock=5,
        )
        self.variant_41 = ProductVariant.objects.create(
            product=self.product, sku='TEST-41', size='41', color='Đen', price=3100000, stock=3,
        )

    def add(self, variant, quantity=1):
        return self.client.post(reverse('cart_add'), {
            'variant_id': variant.id, 'quantity': quantity,
        })

    def test_add_same_sku_twice_combines_quantity(self):
        self.add(self.variant_40, 1)
        self.add(self.variant_40, 2)
        item = CartItem.objects.get(variant=self.variant_40)
        self.assertEqual(item.quantity, 3)

    def test_two_sizes_are_two_cart_items(self):
        self.add(self.variant_40)
        self.add(self.variant_41)
        self.assertEqual(CartItem.objects.count(), 2)

    def test_add_and_update_cannot_exceed_stock(self):
        self.add(self.variant_40, 5)
        self.add(self.variant_40, 1)
        item = CartItem.objects.get(variant=self.variant_40)
        self.assertEqual(item.quantity, 5)
        self.client.post(reverse('cart_item_update', args=[item.id]), {'quantity': 6})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_server_ignores_price_from_request(self):
        self.client.post(reverse('cart_add'), {
            'variant_id': self.variant_40.id, 'quantity': 1, 'price': 1,
        })
        item = CartItem.objects.get(variant=self.variant_40)
        self.assertEqual(item.price_when_added, 3000000)
        self.assertEqual(item.line_total, 3000000)

    def test_delete_item_and_empty_cart_page(self):
        self.add(self.variant_40)
        item = CartItem.objects.get(variant=self.variant_40)
        self.client.post(reverse('cart_item_delete', args=[item.id]))
        self.assertFalse(CartItem.objects.exists())
        self.assertContains(self.client.get(reverse('cart_page')), 'GIỎ HÀNG ĐANG TRỐNG')

    def test_only_selected_items_are_in_cart_total(self):
        self.add(self.variant_40)
        self.add(self.variant_41)
        item = CartItem.objects.get(variant=self.variant_41)
        self.client.post(reverse('cart_item_select', args=[item.id]), {})

        response = self.client.get(reverse('cart_page'))

        self.assertEqual(response.context['cart_total'], 3000000)

    def test_user_cannot_update_another_users_cart_item(self):
        user = User.objects.create(
            username='Owner', email='owner@example.com', phone='0912345678',
            password=make_password('secret123'),
        )
        cart = Cart.objects.create(user=user)
        item = CartItem.objects.create(
            cart=cart, variant=self.variant_40, quantity=1, price_when_added=3000000,
        )

        response = self.client.post(reverse('cart_item_update', args=[item.id]), {'quantity': 2})

        self.assertEqual(response.status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_guest_cart_merges_after_login(self):
        self.add(self.variant_40, 2)
        user = User.objects.create(
            username='Customer', email='customer@example.com', phone='0912345678',
            password=make_password('secret123'),
        )

        self.client.post(reverse('login'), {'email': user.email, 'password': 'secret123'})

        item = CartItem.objects.get(cart__user=user, variant=self.variant_40)
        self.assertEqual(item.quantity, 2)
        self.assertFalse(Cart.objects.filter(session_key__isnull=False).exists())
