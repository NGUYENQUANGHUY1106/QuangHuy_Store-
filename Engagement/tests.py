from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from Login.models import User
from Product.models import Brand, Category, Product, ProductVariant

from .models import RecentlyViewed, WishlistItem


class EngagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='Wishlist User', email='wishlist@example.com', phone='0912345678',
            password=make_password('secret123'),
        )
        brand = Brand.objects.create(name='Nike Wishlist', slug='nike-wishlist')
        shoes = Category.objects.create(name='Giày Wishlist', slug='giay-wishlist')
        shirts = Category.objects.create(name='Áo Wishlist', slug='ao-wishlist')
        self.shoe = Product.objects.create(
            brand=brand, category=shoes, name='Giày yêu thích', slug='giay-yeu-thich',
            price=2000000, image='products/shoe.jpg', material='Da tổng hợp',
        )
        self.shoe_two = Product.objects.create(
            brand=brand, category=shoes, name='Giày so sánh', slug='giay-so-sanh',
            price=2500000, image='products/shoe2.jpg', material='Vải dệt',
        )
        self.shirt = Product.objects.create(
            brand=brand, category=shirts, name='Áo khác loại', slug='ao-khac-loai',
            price=1000000, image='products/shirt.jpg', material='Polyester',
        )
        ProductVariant.objects.create(
            product=self.shoe, sku='WISH-40', size='40', color='Đen', price=2000000, stock=2,
        )
        session = self.client.session
        session['user_id'] = self.user.id
        session.save()

    def test_toggle_wishlist_adds_and_removes_without_duplicates(self):
        url = reverse('wishlist_toggle', args=[self.shoe.id])
        added = self.client.post(url)
        removed = self.client.post(url)

        self.assertTrue(added.json()['added'])
        self.assertFalse(removed.json()['added'])
        self.assertFalse(WishlistItem.objects.exists())

    def test_wishlist_only_contains_current_users_items(self):
        other = User.objects.create(
            username='Other Wishlist', email='other-wishlist@example.com', phone='0987654321',
            password=make_password('secret123'),
        )
        WishlistItem.objects.create(user=self.user, product=self.shoe)
        WishlistItem.objects.create(user=other, product=self.shirt)

        response = self.client.get(reverse('wishlist'))

        self.assertContains(response, self.shoe.name)
        self.assertNotContains(response, self.shirt.name)

    def test_compare_same_category_and_rejects_different_category(self):
        valid = self.client.get(reverse('product_compare'), {'ids': [self.shoe.id, self.shoe_two.id]})
        invalid = self.client.get(reverse('product_compare'), {'ids': [self.shoe.id, self.shirt.id]})

        self.assertContains(valid, 'Da tổng hợp')
        self.assertContains(valid, 'Vải dệt')
        self.assertContains(invalid, 'cùng danh mục')

    def test_product_detail_records_recently_viewed_for_user(self):
        self.client.get(reverse('product_detail', args=[self.shoe.slug]))
        self.client.get(reverse('product_detail', args=[self.shoe_two.slug]))

        self.assertEqual(RecentlyViewed.objects.filter(user=self.user).count(), 2)
        response = self.client.get(reverse('product_detail', args=[self.shirt.slug]))
        self.assertContains(response, self.shoe_two.name)

    def test_guest_recently_viewed_is_saved_in_session(self):
        self.client.session.flush()
        self.client.get(reverse('product_detail', args=[self.shoe.slug]))
        self.client.get(reverse('product_detail', args=[self.shoe_two.slug]))
        self.assertEqual(self.client.session['recent_product_ids'][:2], [self.shoe_two.id, self.shoe.id])
