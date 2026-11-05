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

from .models import Address, PasswordResetToken, User


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

    def test_register_allows_optional_avatar(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'No Avatar', 'email': 'no-avatar@example.com',
            'phone': '0912345678', 'password': 'secret123',
            'confirm_password': 'secret123',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(email='no-avatar@example.com').exists())

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

    def login_user(self, user):
        session = self.client.session
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session.save()

    def test_profile_owner_can_update_personal_information(self):
        user = self.create_user()
        self.login_user(user)

        response = self.client.post(reverse('account'), {
            'username': 'Nguyen Van B',
            'email': 'new@example.com',
            'phone': '0987654321',
        })

        self.assertRedirects(response, reverse('account'))
        user.refresh_from_db()
        self.assertEqual(user.username, 'Nguyen Van B')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.phone, '0987654321')

    def test_address_crud_and_default_selection(self):
        user = self.create_user()
        self.login_user(user)
        first_data = {
            'recipient_name': 'Nguyen Van A', 'phone': '0912345678',
            'province': 'Da Nang', 'ward': 'Hai Chau', 'detail': '12 Tran Phu',
        }
        self.client.post(reverse('address_add'), first_data)
        first = Address.objects.get(user=user)
        self.assertTrue(first.is_default)

        second_data = {
            'recipient_name': 'Nguyen Van B', 'phone': '0987654321',
            'province': 'Ha Noi', 'ward': 'Hoan Kiem', 'detail': '20 Hang Bai',
        }
        self.client.post(reverse('address_add'), second_data)
        second = Address.objects.exclude(id=first.id).get(user=user)
        self.client.post(reverse('address_set_default', args=[second.id]))
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

        second_data['detail'] = '22 Hang Bai'
        self.client.post(reverse('address_edit', args=[second.id]), second_data)
        second.refresh_from_db()
        self.assertEqual(second.detail, '22 Hang Bai')

        self.client.post(reverse('address_delete', args=[second.id]))
        first.refresh_from_db()
        self.assertFalse(Address.objects.filter(id=second.id).exists())
        self.assertTrue(first.is_default)

    def test_address_rejects_invalid_phone(self):
        user = self.create_user()
        self.login_user(user)
        response = self.client.post(reverse('address_add'), {
            'recipient_name': 'Nguyen Van A', 'phone': '123',
            'province': 'Da Nang', 'ward': 'Hai Chau', 'detail': '12 Tran Phu',
        }, follow=True)

        self.assertContains(response, 'Số điện thoại phải gồm 10 chữ số')
        self.assertFalse(Address.objects.filter(user=user).exists())

    def test_user_cannot_access_another_users_address(self):
        owner = self.create_user()
        other = self.create_user('other@example.com', 'Other User')
        address = Address.objects.create(
            user=other, recipient_name='Other User', phone='0987654321',
            province='Ha Noi', ward='Hoan Kiem', detail='20 Hang Bai', is_default=True,
        )
        self.login_user(owner)
        data = {
            'recipient_name': 'Hacker', 'phone': '0912345678',
            'province': 'Da Nang', 'ward': 'Hai Chau', 'detail': 'Changed',
        }

        self.assertEqual(self.client.post(reverse('address_edit', args=[address.id]), data).status_code, 404)
        self.assertEqual(self.client.post(reverse('address_delete', args=[address.id])).status_code, 404)
        self.assertEqual(self.client.post(reverse('address_set_default', args=[address.id])).status_code, 404)
        address.refresh_from_db()
        self.assertEqual(address.detail, '20 Hang Bai')

    def test_change_password_requires_current_password(self):
        user = self.create_user()
        self.login_user(user)
        wrong = self.client.post(reverse('change_password'), {
            'current_password': 'wrong', 'new_password': 'changed123',
            'confirm_password': 'changed123',
        })
        self.assertRedirects(wrong, reverse('account'))
        user.refresh_from_db()
        self.assertTrue(check_password('secret123', user.password))

        success = self.client.post(reverse('change_password'), {
            'current_password': 'secret123', 'new_password': 'changed123',
            'confirm_password': 'changed123',
        })
        self.assertRedirects(success, reverse('account'))
        user.refresh_from_db()
        self.assertTrue(check_password('changed123', user.password))

    def test_address_used_in_order_cannot_be_deleted(self):
        user = self.create_user()
        self.login_user(user)
        address = Address.objects.create(
            user=user, recipient_name='Nguyen Van A', phone='0912345678',
            province='Da Nang', ward='Hai Chau', detail='12 Tran Phu',
            is_default=True, is_used_in_order=True,
        )

        response = self.client.post(reverse('address_delete', args=[address.id]), follow=True)

        self.assertContains(response, 'Không thể xóa địa chỉ đã được dùng trong đơn hàng')
        self.assertTrue(Address.objects.filter(id=address.id).exists())

# Create your tests here.
