import shutil,tempfile
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from Checkout.models import Order,OrderItem,OrderStatusHistory
from Login.models import User
from Product.models import Brand,Category,Product,ProductVariant
from .models import ReturnItem,ReturnRequest

class ReturnsTests(TestCase):
    def setUp(self):
        self.tmp=tempfile.mkdtemp();self.override=self.settings(MEDIA_ROOT=self.tmp);self.override.enable()
        self.user=User.objects.create(username='Return User',email='return@example.com',phone='0912345678',password=make_password('secret123'))
        brand=Brand.objects.create(name='Return Brand');category=Category.objects.create(name='Return Cat')
        product=Product.objects.create(brand=brand,category=category,name='Return Product',price=100,image='x.jpg')
        variant=ProductVariant.objects.create(product=product,sku='RET-1',size='40',color='Đen',price=100,stock=1)
        self.order=Order.objects.create(user=self.user,order_code='QHRET01',idempotency_key='ret-key',status='completed',payment_method='cod',shipping_method='standard',subtotal=200,shipping_fee=0,grand_total=200)
        self.item=OrderItem.objects.create(order=self.order,variant=variant,product_name=product.name,sku=variant.sku,size='40',color='Đen',unit_price=100,quantity=2,line_total=200)
        self.event=OrderStatusHistory.objects.create(order=self.order,status='completed')
        s=self.client.session;s['user_id']=self.user.id;s.save()
    def tearDown(self):self.override.disable();shutil.rmtree(self.tmp,ignore_errors=True)
    def data(self,**extra):
        data={'request_type':'return','order_item_id':self.item.id,'quantity':1,'reason':'Sản phẩm không phù hợp'};data.update(extra);return data
    def test_create_and_prevent_quantity_over_purchase(self):
        self.client.post(reverse('return_create',args=[self.order.order_code]),self.data())
        response=self.client.post(reverse('return_create',args=[self.order.order_code]),self.data(quantity=2),follow=True)
        self.assertEqual(ReturnRequest.objects.count(),1);self.assertContains(response,'không hợp lệ')
    def test_late_or_not_completed_order_is_rejected(self):
        OrderStatusHistory.objects.filter(id=self.event.id).update(created_at=timezone.now()-timedelta(days=8))
        response=self.client.post(reverse('return_create',args=[self.order.order_code]),self.data(),follow=True)
        self.assertContains(response,'không còn đủ điều kiện')
    def test_fake_evidence_is_rejected(self):
        fake=SimpleUploadedFile('fake.txt',b'bad',content_type='text/plain')
        self.client.post(reverse('return_create',args=[self.order.order_code]),self.data(evidence=fake))
        self.assertFalse(ReturnRequest.objects.exists())
    def test_other_user_cannot_view_request(self):
        result=ReturnRequest.objects.create(user=self.user,order=self.order,request_type='return',reason='Reason')
        ReturnItem.objects.create(return_request=result,order_item=self.item,quantity=1)
        other=User.objects.create(username='Other Return',email='other-return@example.com',phone='0987654321',password=make_password('secret123'))
        s=self.client.session;s['user_id']=other.id;s.save()
        self.assertEqual(self.client.get(reverse('return_detail',args=[result.id])).status_code,404)
