import shutil
import tempfile

from django.contrib.auth.hashers import check_password, make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import User


class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.media_override = self.settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_register_creates_user_with_hashed_password(self):
        avatar = SimpleUploadedFile(
            'avatar.png',
            b'fake-image-content',
            content_type='image/png',
        )

        response = self.client.post(
            reverse('register'),
            {
                'full_name': 'Nguyen Van A',
                'email': 'USER@example.com',
                'phone': '0912345678',
                'password': 'secret123',
                'confirm_password': 'secret123',
                'avatar': avatar,
            },
        )

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(email='user@example.com')
        self.assertEqual(user.username, 'Nguyen Van A')
        self.assertTrue(check_password('secret123', user.password))

    def test_login_creates_session(self):
        user = User.objects.create(
            username='Nguyen Van A',
            email='user@example.com',
            phone='0912345678',
            avatar='avatars/example.png',
            password=make_password('secret123'),
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'user@example.com', 'password': 'secret123'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(self.client.session['user_id'], user.id)
        self.assertEqual(self.client.session['email'], user.email)

    def test_home_page_is_available_at_root_url(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'Home.html')
        self.assertContains(response, 'NEW SEASON ESSENTIALS')

    def test_login_rejects_wrong_password(self):
        User.objects.create(
            username='Nguyen Van A',
            email='user@example.com',
            phone='0912345678',
            avatar='avatars/example.png',
            password=make_password('secret123'),
        )

        response = self.client.post(
            reverse('login'),
            {'email': 'user@example.com', 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email hoặc mật khẩu không chính xác.')
        self.assertNotIn('user_id', self.client.session)

# Create your tests here.
