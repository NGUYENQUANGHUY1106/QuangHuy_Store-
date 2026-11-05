import shutil,tempfile
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from Login.models import User
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
