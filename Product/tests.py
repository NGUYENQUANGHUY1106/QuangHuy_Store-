from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Banner, Brand, Category, Product, ProductVariant


class ProductPageTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name='Nike', slug='nike')
        self.category = Category.objects.create(
            name='Giày bóng đá',
            slug='giay-bong-da',
            is_featured=True,
        )

        for number in range(7):
            product = Product.objects.create(
                category=self.category,
                brand=self.brand,
                name=f'Giày bóng đá Nike {number}',
                slug=f'giay-bong-da-nike-{number}',
                price=1000000,
                image=f'products/image-{number}.jpg',
                is_new=True,
                is_best_seller=number == 0,
                discount_percent=10 if number == 1 else 0,
                gender='men' if number % 2 == 0 else 'women',
                popularity=100 - number,
            )
            ProductVariant.objects.create(
                product=product,
                sku=f'NIKE-{number}-42-DEN',
                size='42',
                color='Đen',
                price=1000000 + number * 100000,
                stock=0 if number == 0 else 5,
            )
            ProductVariant.objects.create(
                product=product,
                sku=f'NIKE-{number}-43-TRANG',
                size='43',
                color='Trắng',
                price=1200000 + number * 100000,
                stock=3,
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
        self.assertTemplateUsed(response, 'Product/Category.html')
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_category_pagination_keeps_filter_query_string(self):
        response = self.client.get(
            reverse('product_by_category', args=[self.category.slug]),
            {'brand': 'nike'},
        )

        self.assertEqual(response.context['pagination_query'], 'brand=nike')
        self.assertContains(response, 'brand=nike&amp;page=2')

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
        response = self.client.get(reverse('home'))
        product = response.context['page_obj'][0]

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


class ProductFilterTests(TestCase):
    def setUp(self):
        self.nike = Brand.objects.create(name='Nike', slug='nike')
        self.adidas = Brand.objects.create(name='adidas', slug='adidas')
        self.category = Category.objects.create(name='Giày bóng đá', slug='giay-bong-da')

        self.nike_product = Product.objects.create(
            category=self.category,
            brand=self.nike,
            name='Giày Nike màu đen',
            slug='giay-nike-mau-den',
            price=2000000,
            image='products/nike.jpg',
            gender='men',
            popularity=20,
        )
        ProductVariant.objects.create(
            product=self.nike_product,
            sku='NIKE-42-DEN',
            size='42',
            color='Đen',
            price=2100000,
            stock=8,
        )

        self.adidas_product = Product.objects.create(
            category=self.category,
            brand=self.adidas,
            name='Giày adidas màu trắng',
            slug='giay-adidas-mau-trang',
            price=3000000,
            image='products/adidas.jpg',
            gender='women',
            popularity=50,
        )
        ProductVariant.objects.create(
            product=self.adidas_product,
            sku='ADIDAS-39-TRANG',
            size='39',
            color='Trắng',
            price=3200000,
            stock=0,
        )

    def category_url(self):
        return reverse('product_by_category', args=[self.category.slug])

    def test_combined_filters_return_correct_variant(self):
        response = self.client.get(self.category_url(), {
            'brand': 'nike',
            'gender': 'men',
            'size': '42',
            'color': 'Đen',
            'in_stock': '1',
            'min_price': '2000000',
            'max_price': '2500000',
        })

        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertContains(response, self.nike_product.name.upper())
        self.assertNotContains(response, self.adidas_product.name.upper())

    def test_in_stock_filter_hides_out_of_stock_product(self):
        response = self.client.get(self.category_url(), {'in_stock': '1'})

        self.assertContains(response, self.nike_product.name.upper())
        self.assertNotContains(response, self.adidas_product.name.upper())

    def test_sort_by_price_and_popularity(self):
        price_response = self.client.get(self.category_url(), {'sort': 'price_desc'})
        popular_response = self.client.get(self.category_url(), {'sort': 'popular'})

        self.assertEqual(list(price_response.context['page_obj'])[0], self.adidas_product)
        self.assertEqual(list(popular_response.context['page_obj'])[0], self.adidas_product)

    def test_invalid_price_range_shows_error_without_crashing(self):
        negative_response = self.client.get(self.category_url(), {'min_price': '-1'})
        reversed_response = self.client.get(self.category_url(), {
            'min_price': '4000000',
            'max_price': '1000000',
        })

        self.assertEqual(negative_response.status_code, 200)
        self.assertContains(negative_response, 'phải nằm trong khoảng')
        self.assertContains(reversed_response, 'nhỏ hơn hoặc bằng')

    def test_inactive_product_and_variant_are_hidden(self):
        self.nike_product.is_active = False
        self.nike_product.save()
        self.adidas_product.variants.update(is_active=False)

        response = self.client.get(self.category_url())

        self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_unknown_category_returns_404(self):
        response = self.client.get(reverse('product_by_category', args=['khong-ton-tai']))

        self.assertEqual(response.status_code, 404)

    def test_child_category_products_are_included(self):
        child = Category.objects.create(
            name='Giày sân cỏ nhân tạo',
            slug='giay-san-co-nhan-tao',
            parent=self.category,
        )
        child_product = Product.objects.create(
            category=child,
            brand=self.nike,
            name='Giày Nike TF',
            slug='giay-nike-tf',
            price=2500000,
            image='products/nike-tf.jpg',
        )
        ProductVariant.objects.create(
            product=child_product,
            sku='NIKE-TF-41',
            size='41',
            color='Đen',
            price=2500000,
            stock=4,
        )

        response = self.client.get(self.category_url())

        self.assertContains(response, child_product.name.upper())


class ProductSearchTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name='Nike', slug='nike')
        category = Category.objects.create(name='Giày bóng đá', slug='giay-bong-da')
        self.product = Product.objects.create(
            category=category,
            brand=brand,
            name='Giày Nike Mercurial màu đỏ',
            slug='giay-nike-mercurial-mau-do',
            price=2500000,
            image='products/mercurial.jpg',
            gender='men',
        )
        ProductVariant.objects.create(
            product=self.product,
            sku='NK-MERC-42-RED',
            size='42',
            color='Đỏ',
            price=2600000,
            stock=7,
        )

    def test_search_by_vietnamese_name(self):
        response = self.client.get(reverse('product_search'), {'q': 'giày Nike'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Product/Search.html')
        self.assertContains(response, self.product.name.upper())

    def test_search_by_variant_sku(self):
        response = self.client.get(reverse('product_search'), {'q': 'MERC-42'})

        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertContains(response, self.product.name.upper())

    def test_search_supports_u02_filters(self):
        matching = self.client.get(reverse('product_search'), {
            'q': 'Nike',
            'brand': 'nike',
            'size': '42',
            'color': 'Đỏ',
            'in_stock': '1',
        })
        not_matching = self.client.get(reverse('product_search'), {
            'q': 'Nike',
            'size': '39',
        })

        self.assertEqual(matching.context['page_obj'].paginator.count, 1)
        self.assertEqual(not_matching.context['page_obj'].paginator.count, 0)

    def test_empty_special_and_unknown_queries_are_safe(self):
        empty = self.client.get(reverse('product_search'), {'q': ''})
        special = self.client.get(reverse('product_search'), {'q': '<script>alert(1)</script>'})
        unknown = self.client.get(reverse('product_search'), {'q': 'không tồn tại'})

        self.assertContains(empty, 'NHẬP TỪ KHÓA')
        self.assertNotContains(special, '<script>alert(1)</script>', html=False)
        self.assertContains(special, '&lt;script&gt;')
        self.assertContains(unknown, 'KHÔNG TÌM THẤY SẢN PHẨM')

    def test_search_rejects_query_over_eighty_characters(self):
        response = self.client.get(reverse('product_search'), {'q': 'a' * 81})

        self.assertContains(response, 'không được vượt quá 80 ký tự')
        self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_suggestion_api_returns_product_and_detail_url(self):
        response = self.client.get(reverse('product_suggest'), {'q': 'Mercurial'})
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload['results']), 1)
        self.assertEqual(payload['results'][0]['name'], self.product.name)
        self.assertEqual(
            payload['results'][0]['url'],
            reverse('product_detail', args=[self.product.slug]),
        )

    def test_suggestion_api_requires_two_characters_and_rate_limits(self):
        short_response = self.client.get(reverse('product_suggest'), {'q': 'N'})
        self.assertEqual(short_response.json()['results'], [])

        for _ in range(29):
            self.client.get(reverse('product_suggest'), {'q': 'Nike'})
        limited_response = self.client.get(reverse('product_suggest'), {'q': 'Nike'})

        self.assertEqual(limited_response.status_code, 429)
