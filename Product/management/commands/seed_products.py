from io import BytesIO
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from Product.models import Banner, Brand, Category, Product, ProductImage, vietnamese_slug


BOOT_IMAGES = [
    'https://www.nike.com.pe/on/demandware.static/-/Sites-catalog-equinox/default/dw2059b956/images/hi-res/198729706485_5_20260528-mrtPeru.jpg',
    'https://imgcentauro-a.akamaihd.net/1024x1024/M18UQMQ2A1.jpg',
    'https://static.nike.com/a/images/f_auto/dpr_1.0%2Ccs_srgb/w_1212%2Cc_limit/edc02cce-d60c-4b32-891e-c1775408174f/futbol-ayakkablar-rehberi.jpg',
    'https://2.bp.blogspot.com/-9xBKHKeiWO0/X2hgEtLdRsI/AAAAAAACov4/HfNN5r2vVPo7SQSUAUOZdSf9xe3ua-b9gCNcBGAsYHQ/s1600/nike-flash-crimson-pack%2B%25281%2529.jpg',
    'https://www.gearoutlet.co.uk/cdn/shop/collections/Soccer_Cleats.jpg?v=1707905724',
    'https://onlyfutchuteiras.com/cdn/shop/articles/predator_fd3cacfe-b1c7-44da-bc68-a68863573144.jpg?v=1759684814',
    'https://cdn.sanity.io/images/pu5wtzfc/production/639d9556dffeb3107551096442b098d6bc58fdcc-3000x1875.jpg?h=630&w=1200',
    'https://blog-assets.footy.com/migrated/bfc1e462516841e491270922ed3e4782_Untitled%20design%20%285%29.jpg?width=770',
    'https://file.hstatic.net/1000061481/file/adidas-f50-road-to-glory-2025-13_bb9719b7574f457fa8880e9fde5eefd1_2048x2048.jpg',
    'https://blog-assets.footy.com/migrated/9ce1fb85238640219665fdcabe8b4304_2.jpg?width=770',
    'https://www.nikys-sports.com/cdn/shop/files/AG-Football-Boots_7c895355-78fd-4b62-bc85-8238904cd520_grande.jpg?v=1698942642',
    'https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa,w_600,h_600/global/107826/01/sv01/fnd/PNA/fmt/png/KING-ULTIMATE-Cruyff-Firm-Ground',
    'https://item-shopping.c.yimg.jp/i/n/futaba_107868-03_4_d_20241023110404',
    'https://contents.mediadecathlon.com/m16714816/k%241c180e6a43d51faf2c569638a739ea71/picture.jpg',
]

CLUB_IMAGES = [
    'https://jerseydome.com/cdn/shop/collections/Screenshot_2025-05-31_151823.png?v=1748719130',
    'https://assets.st-note.com/production/uploads/images/177318966/rectangle_large_type_2_a4c6e8bac84d953a3833b321686c8ee8.jpeg?fit=bounds&quality=85&width=1280',
    'https://si.geilicdn.com/open1648936853-1234478995-673e000001977bb3b55e0a22d249_684_761.jpg',
    'https://down-my.img.susercontent.com/file/cn-11134207-7ras8-m2tlk4tuy70t50',
    'https://img1.exportersindia.com/product_images/bc-full/2024/3/13130081/football-jersey-1710560548-7340978.jpg',
    'https://cdn.shopify.com/s/files/1/0613/0427/5199/collections/licensed_jersey612x892.jpg?v=1660787522',
    'https://si.geilicdn.com/open1648936853-1234478995-0f04000001979c68e3240a22d249_800_800.jpg',
    'https://d2io9vrujy7b7u.cloudfront.net/8674712813806/463ccf8d-60b8-4e25-9b26-84acc39b1723/rn_image_picker_lib_temp_6937f254-a241-450e-85b8-4f2d67637a07.jpg',
    'https://si.geilicdn.com/open1754607733-1234478995-27c600000194463a8d200a22d234_800_800.jpg',
    'https://vinsport.vn/my_uploads/2023/09/Bo-quan-ao-da-banh-ao-bong-da-vai-thun-thai-lanh-acrra.jpg',
    'https://www.torshovsport.no/pub_docs/files/Fotball/newDrakter1280x1100.jpg?type=auto&width=1280',
]

NATIONAL_IMAGES = [
    'https://p2-ssl.vatera.hu/photos/fc/21/vilagbajnoksag-2022-katar-valogatott-mezek-nemet-brazil-spanyol-angol-stb-1d3c_1_big.jpg?v=3',
    'https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=958,fit=crop/AGB4brgJzJF7jL41/whatsapp-image-2026-03-14-at-11.00.06-1-RXCJ8SWuV6Wiy7JY.jpeg',
    'https://www.ekinsport.com/media/catalog/category/META-CDM2022.jpg',
    'https://down-br.img.susercontent.com/file/sg-11134201-7rdwk-m12hjfs2ctew95',
    'https://down-my.img.susercontent.com/file/1ff14dd7f93096d9d2797a9beb49b4db',
    'https://s.yimg.com/ny/api/res/1.2/Pyr47gchdoc473XR5WdQvQ--/YXBwaWQ9aGlnaGxhbmRlcjt3PTk2MDtoPTcwOTtjZj13ZWJw/https%3A/media.zenfs.com/en/homerun/feed_manager_auto_publish_494/b3f7fa6899ccf1b32d7fb598d50fb536',
    'https://static.independent.co.uk/2022/11/07/14/Blank%209%20Grids%20Collage.png?auto=webp&width=1200',
    'https://cametbol.com/image/cache/catalog/Blog2026/melhores-camisas-copa-do-mundo-2026-as-5-mais-bonitas-2280x800w.png',
    'https://si.geilicdn.com/open1710213539-1234478995-0bbd0000019de9e3060d0a22d249_1200_1200.jpg',
    'https://media.karousell.com/media/photos/products/2026/8/9/_clearing_2026_world_cup_jerse_1786262866_cebaf040.jpg',
    'https://amzunit.com/cdn/shop/files/hf_20260429_151951_048683b5-9ed0-44de-90dd-1c54c50670c8.png?v=1777476330&width=1200',
]

SHORT_IMAGES = [
    'https://shop.r10s.jp/shoes-iland/cabinet/300017/8401-445-1937-24.jpg',
    'https://cdn.011st.com/11dims/resize/2000x2000/quality/75/11src/pd/v2/4/3/6/8/6/3/EBWRr/56436863_B.jpg',
    'https://www.fripdrop.com/149-large_default/box-shorts-de-sport-de-marques.jpg',
    'https://shop.r10s.jp/elephant-sports/cabinet/image222/706377-1.jpg',
    'https://down-br.img.susercontent.com/file/br-11134207-7qukw-lg5agv22q0vy67',
    'https://www.soccerevolution.com/store/images/retail/_hi_res/PUM_42017_A_big.jpg',
    'https://curva-app.nyc3.cdn.digitaloceanspaces.com/assets/uploads/products/1747568155-1746360239.8708.webp?v=1',
    'https://www.supremeteamwear.com.au/cdn/shop/files/705752_puma-short-red.jpg?v=1704329885&width=600',
]

CATEGORY_DATA = [
    {
        'name': 'Giày bóng đá',
        'slug': 'giay-bong-da',
        'images': BOOT_IMAGES,
        'products': [
            ('Giày Nike Mercurial Vapor 17 Elite sân cỏ tự nhiên', 'Nike', 7479000),
            ('Giày Nike Mercurial Vapor 17 Academy sân cỏ nhân tạo', 'Nike', 2629000),
            ('Giày Nike Phantom 6 Low Elite kiểm soát bóng', 'Nike', 7629000),
            ('Giày Nike Phantom 6 Low Pro sân cỏ nhân tạo', 'Nike', 4109000),
            ('Giày Nike Tiempo Maestro Academy đa mặt sân', 'Nike', 2479000),
            ('Giày adidas F50 Hyperfast Elite sân cỏ tự nhiên', 'adidas', 6500000),
            ('Giày adidas Predator Elite lưỡi gà gập', 'adidas', 6700000),
            ('Giày adidas Copa Pure IV Elite sân cỏ tự nhiên', 'adidas', 5500000),
            ('Giày adidas F50 League sân cỏ nhân tạo', 'adidas', 2400000),
            ('Giày adidas Predator League sân cứng', 'adidas', 2700000),
            ('Giày Puma Future Ultimate FG AG', 'Puma', 4590000),
            ('Giày Puma King Ultimate Cruyff FG AG', 'Puma', 4990000),
            ('Giày Puma Ultra Ultimate tốc độ', 'Puma', 4290000),
            ('Giày Puma King Ultimate sân cỏ nhân tạo', 'Puma', 3990000),
        ],
    },
    {
        'name': 'Áo quần câu lạc bộ',
        'slug': 'ao-quan-clb',
        'images': CLUB_IMAGES,
        'products': [
            ('Áo đấu sân nhà Real Madrid', 'adidas', 1890000),
            ('Áo đấu sân nhà Arsenal', 'adidas', 1790000),
            ('Áo đấu sân nhà Manchester United', 'adidas', 1790000),
            ('Áo đấu sân nhà Liverpool', 'adidas', 1790000),
            ('Áo đấu sân nhà Bayern Munich', 'adidas', 1690000),
            ('Áo đấu sân nhà Juventus', 'adidas', 1690000),
            ('Áo đấu sân nhà Barcelona', 'Nike', 1890000),
            ('Áo đấu sân nhà Paris Saint Germain', 'Nike', 1890000),
            ('Áo đấu sân nhà Chelsea', 'Nike', 1790000),
            ('Áo đấu sân nhà Tottenham', 'Nike', 1690000),
            ('Áo đấu sân nhà Manchester City', 'Puma', 1790000),
            ('Áo đấu sân nhà AC Milan', 'Puma', 1690000),
            ('Áo đấu sân nhà Dortmund', 'Puma', 1590000),
            ('Bộ quần áo thi đấu Inter Milan', 'Nike', 1990000),
        ],
    },
    {
        'name': 'Áo đội tuyển quốc gia',
        'slug': 'ao-doi-tuyen-quoc-gia',
        'images': NATIONAL_IMAGES,
        'products': [
            ('Áo đội tuyển Việt Nam sân nhà', 'Nike', 990000),
            ('Áo đội tuyển Argentina sân nhà', 'adidas', 1790000),
            ('Áo đội tuyển Brazil sân nhà', 'Nike', 1790000),
            ('Áo đội tuyển Pháp sân nhà', 'Nike', 1790000),
            ('Áo đội tuyển Đức sân nhà', 'adidas', 1690000),
            ('Áo đội tuyển Tây Ban Nha sân nhà', 'adidas', 1690000),
            ('Áo đội tuyển Bồ Đào Nha sân nhà', 'Puma', 1690000),
            ('Áo đội tuyển Anh sân nhà', 'Nike', 1790000),
            ('Áo đội tuyển Ý sân nhà', 'adidas', 1690000),
            ('Áo đội tuyển Hà Lan sân nhà', 'Nike', 1690000),
            ('Áo đội tuyển Nhật Bản sân nhà', 'adidas', 1590000),
            ('Áo đội tuyển Hàn Quốc sân nhà', 'Nike', 1590000),
            ('Áo đội tuyển Croatia sân nhà', 'Nike', 1590000),
            ('Áo đội tuyển Bỉ sân nhà', 'adidas', 1590000),
        ],
    },
    {
        'name': 'Quần bóng đá',
        'slug': 'quan-bong-da',
        'images': SHORT_IMAGES,
        'products': [
            ('Quần bóng đá Nike Dri FIT màu đen', 'Nike', 590000),
            ('Quần bóng đá Nike Dri FIT màu trắng', 'Nike', 590000),
            ('Quần bóng đá adidas Tiro màu xanh navy', 'adidas', 650000),
            ('Quần bóng đá adidas Entrada màu đen', 'adidas', 550000),
            ('Quần bóng đá Puma TeamLiga màu đỏ', 'Puma', 490000),
            ('Quần bóng đá Puma TeamGoal màu xanh', 'Puma', 490000),
            ('Quần tập bóng đá adidas Aeroready', 'adidas', 690000),
            ('Quần tập bóng đá Nike Academy', 'Nike', 690000),
        ],
    },
]


class Command(BaseCommand):
    help = 'Tạo danh mục, thương hiệu, banner và 50 sản phẩm bóng đá mẫu.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh-images',
            action='store_true',
            help='Tải lại ảnh cho các sản phẩm đã tồn tại.',
        )

    def download_as_jpeg(self, image_url):
        request = Request(image_url, headers={'User-Agent': 'Mozilla/5.0 QuangHuyStore/1.0'})
        with urlopen(request, timeout=40) as response:
            image_data = response.read()

        image = Image.open(BytesIO(image_data)).convert('RGB')
        image.thumbnail((1000, 1000))
        output = BytesIO()
        image.save(output, format='JPEG', quality=90, optimize=True)
        return output.getvalue()

    def save_remote_image(self, instance, image_url, filename):
        if image_url in self.failed_urls:
            return False

        content = self.image_cache.get(image_url)
        if content is None:
            try:
                content = self.download_as_jpeg(image_url)
                self.image_cache[image_url] = content
            except Exception as error:
                self.failed_urls.add(image_url)
                self.stderr.write(f'Khong tai duoc nguon anh: {error}')
                return False

        if instance.image:
            instance.image.delete(save=False)
        instance.image.save(filename, ContentFile(content), save=False)
        return True

    def handle(self, *args, **options):
        refresh_images = options['refresh_images']
        self.image_cache = {}
        self.failed_urls = set()
        total = 0

        brands = {
            name: Brand.objects.update_or_create(
                slug=vietnamese_slug(name),
                defaults={'name': name, 'is_active': True},
            )[0]
            for name in ['Nike', 'adidas', 'Puma']
        }

        for order, category_data in enumerate(CATEGORY_DATA, start=1):
            category, _ = Category.objects.update_or_create(
                slug=category_data['slug'],
                defaults={
                    'name': category_data['name'],
                    'order': order,
                    'is_active': True,
                    'is_featured': True,
                },
            )
            existing_products = list(category.products.order_by('id'))

            for index, (name, brand_name, price) in enumerate(category_data['products']):
                if index < len(existing_products):
                    product = existing_products[index]
                else:
                    product = Product(category=category)

                product.category = category
                product.brand = brands[brand_name]
                product.name = name
                product.slug = vietnamese_slug(name)
                product.price = price
                product.description = f'Sản phẩm bóng đá {brand_name} với thiết kế thể thao hiện đại.'
                old_source_url = product.source_url
                preferred_image = category_data['images'][index % len(category_data['images'])]
                product.is_new = index < 6
                product.is_best_seller = index % 3 == 0
                product.discount_percent = 20 if index % 5 == 0 else (10 if index % 4 == 0 else 0)
                product.is_active = True

                if refresh_images or not product.image:
                    fallback_images = category_data['images']
                    if category.slug == 'giay-bong-da':
                        brand_ranges = {
                            'Nike': BOOT_IMAGES[:5],
                            'adidas': BOOT_IMAGES[5:10],
                            'Puma': BOOT_IMAGES[10:],
                        }
                        fallback_images = brand_ranges[brand_name]

                    candidates = [preferred_image] + [
                        url for url in fallback_images if url != preferred_image
                    ]
                    image_saved = False
                    for image_url in candidates:
                        if self.save_remote_image(product, image_url, f'{product.slug}.jpg'):
                            product.source_url = image_url
                            image_saved = True
                            break
                    if not image_saved:
                        product.source_url = old_source_url
                elif not product.source_url:
                    product.source_url = preferred_image

                product.save()
                if product.image:
                    ProductImage.objects.update_or_create(
                        product=product,
                        order=0,
                        defaults={
                            'image': product.image.name,
                            'alt_text': product.name,
                        },
                    )
                total += 1

            for old_product in existing_products[len(category_data['products']):]:
                old_product.delete()

            self.stdout.write(f'Da xu ly: {category.slug}')

        banner, _ = Banner.objects.update_or_create(
            title='TỐC ĐỘ. KIỂM SOÁT. ĐAM MÊ.',
            defaults={
                'subtitle': 'Khám phá giày và trang phục bóng đá từ Nike, adidas và Puma.',
                'link_text': 'KHÁM PHÁ BỘ SƯU TẬP',
                'link_url': '#products',
                'is_active': True,
                'order': 1,
            },
        )
        if refresh_images or not banner.image:
            self.save_remote_image(banner, BOOT_IMAGES[6], 'banner-bong-da.jpg')
            banner.save()

        self.stdout.write(self.style.SUCCESS(f'Hoan thanh {total} san pham.'))
