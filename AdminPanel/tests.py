from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AuditLog, StaffProfile
from .permissions import has_admin_permission
from .services import menu_for_user


class AdminAuthenticationTests(TestCase):
    def create_staff(self, username='order_staff', role='ORDER', password='StrongPass123'):
        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password=password,
            is_staff=True,
        )
        StaffProfile.objects.create(user=user, role=role)
        return user

    def test_anonymous_user_is_redirected_to_admin_login(self):
        response = self.client.get(reverse('admin_panel:dashboard'))

        expected = f"{reverse('admin_panel:login')}?next={reverse('admin_panel:dashboard')}"
        self.assertRedirects(response, expected)

    def test_staff_with_role_can_login_and_open_dashboard(self):
        user = self.create_staff()

        response = self.client.post(reverse('admin_panel:login'), {
            'username': user.username,
            'password': 'StrongPass123',
        })

        self.assertRedirects(response, reverse('admin_panel:dashboard'))
        self.assertContains(self.client.get(reverse('admin_panel:dashboard')), user.username)
        self.assertTrue(AuditLog.objects.filter(actor=user, action='admin.login').exists())

    def test_normal_or_unassigned_account_cannot_login(self):
        User = get_user_model()
        normal = User.objects.create_user(username='normal', password='StrongPass123')
        no_profile = User.objects.create_user(username='staff', password='StrongPass123', is_staff=True)

        normal_response = self.client.post(reverse('admin_panel:login'), {
            'username': normal.username, 'password': 'StrongPass123',
        })
        staff_response = self.client.post(reverse('admin_panel:login'), {
            'username': no_profile.username, 'password': 'StrongPass123',
        })

        self.assertContains(normal_response, 'quyền nhân viên không hợp lệ')
        self.assertContains(staff_response, 'quyền nhân viên không hợp lệ')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_rejects_unsafe_next_url(self):
        user = self.create_staff()
        response = self.client.post(reverse('admin_panel:login'), {
            'username': user.username,
            'password': 'StrongPass123',
            'next': 'https://evil.example/steal',
        })
        self.assertRedirects(response, reverse('admin_panel:dashboard'))

    def test_login_is_rate_limited_after_ten_failures(self):
        for _ in range(10):
            self.client.post(reverse('admin_panel:login'), {
                'username': 'unknown', 'password': 'wrong',
            })

        response = self.client.post(reverse('admin_panel:login'), {
            'username': 'unknown', 'password': 'wrong',
        })

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, '5 phút', status_code=429)

    def test_logout_uses_post_and_writes_audit_log(self):
        user = self.create_staff()
        self.client.force_login(user)

        get_response = self.client.get(reverse('admin_panel:logout'))
        post_response = self.client.post(reverse('admin_panel:logout'))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse('admin_panel:login'))
        self.assertTrue(AuditLog.objects.filter(actor=user, action='admin.logout').exists())


class AdminPermissionTests(TestCase):
    def create_staff(self, username, role):
        User = get_user_model()
        user = User.objects.create_user(username=username, password='StrongPass123', is_staff=True)
        StaffProfile.objects.create(user=user, role=role)
        return user

    def test_role_permission_matrix_allows_only_assigned_module(self):
        product_staff = self.create_staff('product_staff', 'PRODUCT')

        self.assertTrue(has_admin_permission(product_staff, 'products.change'))
        self.assertFalse(has_admin_permission(product_staff, 'finance.view'))

    def test_superuser_has_all_admin_permissions(self):
        User = get_user_model()
        superuser = User.objects.create_superuser('root', 'root@example.com', 'StrongPass123')

        self.assertTrue(has_admin_permission(superuser, 'staff.manage_permissions'))
        self.assertTrue(has_admin_permission(superuser, 'anything.future'))

    def test_staff_cannot_call_endpoint_without_permission(self):
        user = self.create_staff('order_staff', 'ORDER')
        self.client.force_login(user)

        response = self.client.get(reverse('admin_panel:permission_test'))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'AdminPanel/Forbidden.html')

    def test_superuser_can_call_sensitive_endpoint(self):
        User = get_user_model()
        user = User.objects.create_superuser('root', 'root@example.com', 'StrongPass123')
        self.client.force_login(user)

        response = self.client.get(reverse('admin_panel:permission_test'))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'allowed': True})

    def test_menu_only_contains_modules_for_role(self):
        user = self.create_staff('support_staff', 'SUPPORT')
        labels = [item['label'] for item in menu_for_user(user)]

        self.assertIn('Tổng quan', labels)
        self.assertIn('Hỗ trợ', labels)
        self.assertNotIn('Tài chính', labels)
        self.assertNotIn('Kho hàng', labels)

    def test_me_endpoint_returns_current_staff_role(self):
        user = self.create_staff('finance_staff', 'FINANCE')
        self.client.force_login(user)

        response = self.client.get(reverse('admin_panel:me'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], 'FINANCE')
        self.assertEqual(response.json()['id'], user.id)

    def test_role_change_and_revocation_apply_during_current_session(self):
        user = self.create_staff('changing_staff', 'ORDER')
        self.client.force_login(user)
        self.assertTrue(has_admin_permission(user, 'orders.change'))

        profile = user.staff_profile
        profile.role = 'SUPPORT'
        profile.save(update_fields=['role'])
        user.refresh_from_db()
        self.assertFalse(has_admin_permission(user, 'orders.change'))
        self.assertTrue(has_admin_permission(user, 'support.change'))

        user.is_staff = False
        user.save(update_fields=['is_staff'])
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 403)


class AdminPasswordTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='staff', password='OldPassword123', is_staff=True,
        )
        StaffProfile.objects.create(user=self.user, role='ORDER')
        self.client.force_login(self.user)

    def test_password_change_keeps_session_and_writes_audit(self):
        response = self.client.post(reverse('admin_panel:change_password'), {
            'old_password': 'OldPassword123',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        })

        self.assertRedirects(response, reverse('admin_panel:change_password'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword456!'))
        self.assertIn('_auth_user_id', self.client.session)
        self.assertTrue(AuditLog.objects.filter(actor=self.user, action='admin.password_changed').exists())

    def test_wrong_current_password_is_rejected(self):
        response = self.client.post(reverse('admin_panel:change_password'), {
            'old_password': 'WrongPassword',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123'))

