import shutil
import tempfile

from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from Checkout.models import Order, OrderItem
from Login.models import User
from Product.models import Brand, Category, Product, ProductVariant

from .models import ProductQuestion, Review


class ReviewTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = self.settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.user = User.objects.create(
            username='Review User', email='review@example.com', phone='0912345678',
            password=make_password('secret123'),
        )
        brand = Brand.objects.create(name='Nike Review', slug='nike-review')
        category = Category.objects.create(name='Review Category', slug='review-category')
        self.product = Product.objects.create(
            brand=brand, category=category, name='Sản phẩm đánh giá', slug='san-pham-danh-gia',
            price=1000000, image='products/review.jpg',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku='REVIEW-40', size='40', color='Đen', price=1000000, stock=5,
        )
        session = self.client.session
        session['user_id'] = self.user.id
        session.save()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def completed_order_item(self):
        order = Order.objects.create(
            user=self.user, order_code='QHREVIEW01', idempotency_key='review-key',
            status='completed', payment_method='cod', shipping_method='standard',
            subtotal=1000000, shipping_fee=0, grand_total=1000000,
        )
        return OrderItem.objects.create(
            order=order, variant=self.variant, product_name=self.product.name,
            sku=self.variant.sku, size='40', color='Đen', unit_price=1000000,
            quantity=1, line_total=1000000,
        )

    def test_user_must_have_completed_purchase(self):
        response = self.client.post(reverse('review_create', args=[self.product.id]), {
            'rating': 5, 'comment': 'Sản phẩm rất tốt',
        }, follow=True)
        self.assertContains(response, 'chỉ có thể đánh giá sản phẩm đã mua')
        self.assertFalse(Review.objects.exists())

    def test_create_review_is_verified_and_duplicate_is_rejected(self):
        self.completed_order_item()
        url = reverse('review_create', args=[self.product.id])
        self.client.post(url, {'rating': 5, 'comment': 'Sản phẩm rất tốt'})
        duplicate = self.client.post(url, {'rating': 4, 'comment': 'Đánh giá lần hai'}, follow=True)

        review = Review.objects.get()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.order_item.order.status, 'completed')
        self.assertContains(duplicate, 'đã đánh giá sản phẩm này')
        self.assertEqual(Review.objects.count(), 1)

    def test_invalid_rating_and_fake_image_are_rejected(self):
        self.completed_order_item()
        invalid = self.client.post(reverse('review_create', args=[self.product.id]), {
            'rating': 6, 'comment': 'Không hợp lệ',
        })
        fake = SimpleUploadedFile('fake.txt', b'not-image', content_type='text/plain')
        fake_response = self.client.post(reverse('review_create', args=[self.product.id]), {
            'rating': 5, 'comment': 'Có ảnh giả', 'images': fake,
        }, follow=True)

        self.assertEqual(invalid.status_code, 302)
        self.assertContains(fake_response, 'phải là hình ảnh')
        self.assertFalse(Review.objects.exists())

    def test_user_cannot_edit_or_delete_another_users_review(self):
        order_item = self.completed_order_item()
        other = User.objects.create(
            username='Other Reviewer', email='other-review@example.com', phone='0987654321',
            password=make_password('secret123'),
        )
        review = Review.objects.create(
            user=other, product=self.product, order_item=order_item,
            rating=4, comment='Review của người khác',
        )
        self.assertEqual(self.client.post(reverse('review_edit', args=[review.id]), {'rating': 1, 'comment': 'Hacked'}).status_code, 404)
        self.assertEqual(self.client.post(reverse('review_delete', args=[review.id])).status_code, 404)

    def test_review_output_is_escaped_and_rating_is_aggregated(self):
        order_item = self.completed_order_item()
        Review.objects.create(
            user=self.user, product=self.product, order_item=order_item,
            rating=4, comment='<script>alert(1)</script>',
        )
        response = self.client.get(reverse('product_detail', args=[self.product.slug]))
        self.assertContains(response, '4.0/5 SAO')
        self.assertContains(response, '&lt;script&gt;', html=False)
        self.assertNotContains(response, '<script>alert(1)</script>', html=False)

    def test_logged_in_user_can_ask_product_question(self):
        response = self.client.post(reverse('question_create', args=[self.product.id]), {
            'question': 'Sản phẩm này còn size 41 không?',
        })
        self.assertRedirects(response, reverse('product_detail', args=[self.product.slug]))
        self.assertTrue(ProductQuestion.objects.filter(user=self.user, product=self.product).exists())
