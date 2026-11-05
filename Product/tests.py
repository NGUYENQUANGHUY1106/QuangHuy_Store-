from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Banner, Brand, Category, Product


class ProductPageTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='Nike', slug='nike')
        self.category = Category.objects.create(
            name='Giày bóng đá',
            slug='giay-bong-da',
            is_featured=True,
        )

        for number in range(7):
            Product.objects.create(
                category=self.category,
                brand=self.brand,
                name=f'Giày bóng đá Nike {number}',
                slug=f'giay-bong-da-nike-{number}',
                price=1000000,
                image=f'products/image-{number}.jpg',
                is_new=True,
                is_best_seller=number == 0,
                discount_percent=10 if number == 1 else 0,
            )

    def test_home_page_has_six_products_per_page(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(len(response.context['page_obj']), 6)
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 2)

    def test_home_has_required_u01_sections(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'DANH MỤC NỔI BẬT')
        self.assertContains(response, 'HÀNG MỚI')
        self.assertContains(response, 'BÁN CHẠY')
        self.assertContains(response, 'KHUYẾN MÃI')
        self.assertContains(response, 'Tìm sản phẩm')

    def test_category_is_displayed_in_menu(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'GIÀY BÓNG ĐÁ')

    def test_filter_products_by_category(self):
        response = self.client.get(reverse('product_by_category', args=[self.category.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_category'], self.category)

    def test_search_finds_product_by_vietnamese_name(self):
        response = self.client.get(reverse('home'), {'q': 'Nike 3'})

        self.assertContains(response, 'GIÀY BÓNG ĐÁ NIKE 3')
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_hidden_product_is_not_displayed(self):
        hidden = Product.objects.first()
        hidden.is_active = False
        hidden.save()

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, hidden.name.upper())
        self.assertEqual(response.context['page_obj'].paginator.count, 6)

    def test_product_card_links_to_detail_page(self):
        product = Product.objects.first()
        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('product_detail', args=[product.slug]))

        detail_response = self.client.get(reverse('product_detail', args=[product.slug]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertTemplateUsed(detail_response, 'Product/Detail.html')
        self.assertContains(detail_response, product.name)

    def test_inactive_product_detail_returns_404(self):
        product = Product.objects.first()
        product.is_active = False
        product.save()

        response = self.client.get(reverse('product_detail', args=[product.slug]))

        self.assertEqual(response.status_code, 404)

    def test_banner_only_displays_inside_publish_time(self):
        Banner.objects.create(
            title='Banner đang chạy',
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        Banner.objects.create(
            title='Banner chưa chạy',
            starts_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Banner đang chạy')
        self.assertNotContains(response, 'Banner chưa chạy')

    def test_empty_search_and_footer_links(self):
        response = self.client.get(reverse('home'), {'q': 'không tồn tại'})

        self.assertContains(response, 'CHƯA TÌM THẤY SẢN PHẨM')
        self.assertContains(response, reverse('information_page', args=['lien-he']))
        self.assertContains(response, reverse('information_page', args=['chinh-sach']))
        self.assertContains(response, reverse('information_page', args=['huong-dan-size']))
