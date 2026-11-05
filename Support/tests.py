import shutil,tempfile
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from Login.models import User
from Product.models import Brand,Category,Product
from .models import Notification,SupportTicket

class SupportTests(TestCase):
    def setUp(self):
        self.tmp=tempfile.mkdtemp();self.override=self.settings(MEDIA_ROOT=self.tmp);self.override.enable()
        self.user=User.objects.create(username='Support User',email='support-user@example.com',phone='0912345678',password=make_password('secret123'))
        s=self.client.session;s['user_id']=self.user.id;s.save()
    def tearDown(self):self.override.disable();shutil.rmtree(self.tmp,ignore_errors=True)
    def test_notification_can_be_marked_read(self):
        item=Notification.objects.create(user=self.user,title='Test',message='Message')
        self.client.post(reverse('notification_read',args=[item.id]));item.refresh_from_db();self.assertTrue(item.is_read)
    def test_ticket_is_private(self):
        ticket=SupportTicket.objects.create(user=self.user,category='Đơn hàng',subject='Cần hỗ trợ')
        other=User.objects.create(username='Other Support',email='other-support@example.com',phone='0987654321',password=make_password('secret123'))
        s=self.client.session;s['user_id']=other.id;s.save()
        self.assertEqual(self.client.get(reverse('ticket_detail',args=[ticket.id])).status_code,404)
    def test_ticket_spam_limit_and_fake_file(self):
        data={'category':'Đơn hàng','subject':'Cần hỗ trợ đơn','message':'Nội dung cần hỗ trợ đủ dài'}
        for number in range(3):self.client.post(reverse('ticket_create'),data)
        blocked=self.client.post(reverse('ticket_create'),data,follow=True)
        self.assertContains(blocked,'quá nhanh');self.assertEqual(SupportTicket.objects.count(),3)
        session=self.client.session;session['ticket_times']=[];session.save()
        fake=SimpleUploadedFile('bad.exe',b'bad',content_type='application/octet-stream')
        self.client.post(reverse('ticket_create'),{**data,'attachment':fake})
        self.assertEqual(SupportTicket.objects.count(),3)

class SiteQualityTests(TestCase):
    def setUp(self):
        brand=Brand.objects.create(name='SEO Brand',slug='seo-brand')
        category=Category.objects.create(name='SEO Category',slug='seo-category',seo_title='Danh mục SEO',meta_description='Mô tả danh mục SEO')
        self.product=Product.objects.create(brand=brand,category=category,name='SEO Product',slug='seo-product',price=100,image='seo.jpg',seo_title='Sản phẩm SEO',meta_description='Mô tả sản phẩm SEO')
    def test_static_pages_sitemap_and_robots(self):
        page=self.client.get(reverse('static_page',args=['quyen-rieng-tu']))
        sitemap=self.client.get(reverse('sitemap'));robots=self.client.get(reverse('robots'))
        self.assertContains(page,'QUYỀN RIÊNG TƯ')
        self.assertContains(sitemap,'/product/seo-product/')
        self.assertContains(robots,'Disallow: /account/')
    def test_metadata_canonical_and_private_noindex(self):
        product=self.client.get(reverse('product_detail',args=[self.product.slug]))
        cart=self.client.get(reverse('cart_page'))
        self.assertContains(product,'Sản phẩm SEO | QuangHuy Store')
        self.assertContains(product,'rel="canonical"')
        self.assertContains(cart,'noindex, nofollow')
    def test_custom_404_is_helpful(self):
        with self.settings(DEBUG=False,ALLOWED_HOSTS=['testserver']):
            response=self.client.get('/duong-dan-khong-ton-tai/')
        self.assertEqual(response.status_code,404)
        self.assertContains(response,'KHÔNG TÌM THẤY TRANG',status_code=404)
