import shutil
import tempfile
import re
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PasswordResetToken, User


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
        self.assertTemplateUsed(response, 'Product/Home.html')
        self.assertContains(response, 'TẤT CẢ SẢN PHẨM')

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

    def test_login_rate_limit_after_ten_failed_attempts(self):
        self.create_user()
        for _ in range(10):
            self.client.post(reverse('login'), {
                'email': 'user@example.com', 'password': 'wrong-password',
            })

        response = self.client.post(reverse('login'), {
            'email': 'user@example.com', 'password': 'wrong-password',
        })

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, '5 phút', status_code=429)

    def create_user(self, email='user@example.com', username='Nguyen Van A'):
        return User.objects.create(
            username=username,
            email=email,
            phone='0912345678',
            avatar='avatars/example.png',
            password=make_password('secret123'),
        )

    def test_register_rejects_duplicate_email_and_username(self):
        self.create_user()
        avatar = SimpleUploadedFile('avatar.png', b'image', content_type='image/png')
        duplicate_email = self.client.post(reverse('register'), {
            'full_name': 'Another Name', 'email': 'USER@example.com', 'phone': '0912345679',
            'password': 'secret456', 'confirm_password': 'secret456', 'avatar': avatar,
        })
        avatar2 = SimpleUploadedFile('avatar2.png', b'image', content_type='image/png')
        duplicate_name = self.client.post(reverse('register'), {
            'full_name': 'nguyen van a', 'email': 'other@example.com', 'phone': '0912345679',
            'password': 'secret456', 'confirm_password': 'secret456', 'avatar': avatar2,
        })

        self.assertContains(duplicate_email, 'Email này đã được đăng ký')
        self.assertContains(duplicate_name, 'Tên tài khoản này đã được sử dụng')

    def test_account_is_protected_and_login_respects_safe_next(self):
        user = self.create_user()
        protected = self.client.get(reverse('account'))
        self.assertRedirects(protected, f"{reverse('login')}?next={reverse('account')}")

        response = self.client.post(reverse('login'), {
            'email': user.email, 'password': 'secret123', 'next': reverse('account'),
        })
        self.assertRedirects(response, reverse('account'))
        self.assertContains(self.client.get(reverse('account')), user.email)

        external = self.client.post(reverse('login'), {
            'email': user.email, 'password': 'secret123', 'next': 'https://evil.example/',
        })
        self.assertRedirects(external, reverse('home'))

    def test_logout_clears_user_but_preserves_guest_cart(self):
        user = self.create_user()
        session = self.client.session
        session['user_id'] = user.id
        session['cart'] = {'12': 2}
        session['cart_count'] = 2
        session.save()

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('user_id', self.client.session)
        self.assertEqual(self.client.session['cart_count'], 2)

    def test_forgot_password_does_not_reveal_email_existence(self):
        self.create_user()
        known = self.client.post(reverse('forgot_password'), {'email': 'user@example.com'}, follow=True)
        unknown = self.client.post(reverse('forgot_password'), {'email': 'unknown@example.com'}, follow=True)

        message = 'Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi.'
        self.assertContains(known, message)
        self.assertContains(unknown, message)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_token_is_single_use(self):
        user = self.create_user()
        self.client.post(reverse('forgot_password'), {'email': user.email})
        token = re.search(r'/reset-password/([^/]+)/', mail.outbox[0].body).group(1)
        reset_url = reverse('reset_password', args=[token])

        response = self.client.post(reset_url, {
            'password': 'newsecret123', 'confirm_password': 'newsecret123',
        })
        self.assertRedirects(response, reverse('login'))
        user.refresh_from_db()
        self.assertTrue(check_password('newsecret123', user.password))

        reused = self.client.get(reset_url)
        self.assertContains(reused, 'đã hết hạn hoặc đã được sử dụng')

    def test_expired_password_reset_token_is_rejected(self):
        user = self.create_user()
        raw_token = 'expired-token'
        import hashlib
        PasswordResetToken.objects.create(
            user=user,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.post(reverse('reset_password', args=[raw_token]), {
            'password': 'newsecret123', 'confirm_password': 'newsecret123',
        })

        self.assertContains(response, 'đã hết hạn hoặc đã được sử dụng')
        user.refresh_from_db()
        self.assertTrue(check_password('secret123', user.password))

# Create your tests here.
