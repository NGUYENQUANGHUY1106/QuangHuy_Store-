from datetime import timedelta
from decimal import Decimal
import base64

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from Checkout.models import Order,OrderItem
from Inventory.models import Stock,Warehouse
from Login.models import User as Customer
from Payment.models import Payment
from Product.models import Brand, Category, Product, ProductVariant, SportType

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


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            username='Khách dashboard', email='dashboard@example.com',
            phone='0912345678', password='hashed',
        )
        category = Category.objects.create(name='Dashboard category', slug='dashboard-category')
        brand = Brand.objects.create(name='Dashboard brand', slug='dashboard-brand')
        product = Product.objects.create(
            category=category, brand=brand, name='Sản phẩm dashboard',
            slug='san-pham-dashboard', price=Decimal('1000000'), image='products/dashboard.jpg',
        )
        self.low_variant = ProductVariant.objects.create(
            product=product, sku='DASH-40', size='40', color='Đen',
            price=Decimal('1000000'), stock=3,
        )

    def create_staff(self, username, role):
        User = get_user_model()
        user = User.objects.create_user(username=username, password='StrongPass123', is_staff=True)
        StaffProfile.objects.create(user=user, role=role)
        return user

    def create_order(self, code, status='completed', amount=Decimal('1000000'), days_ago=0, paid=True):
        order = Order.objects.create(
            user=self.customer,
            order_code=code,
            idempotency_key=f'key-{code}',
            status=status,
            payment_method='cod',
            shipping_method='standard',
            subtotal=amount,
            shipping_fee=0,
            grand_total=amount,
        )
        created_at = timezone.now() - timedelta(days=days_ago)
        Order.objects.filter(pk=order.pk).update(created_at=created_at)
        payment = Payment.objects.create(
            order=order,
            status='paid' if paid else 'pending',
            amount=amount,
            paid_at=created_at if paid else None,
        )
        return order, payment

    def test_finance_dashboard_shows_reconciled_revenue(self):
        self.create_order('PAID-01', amount=Decimal('1200000'))
        self.create_order('CANCEL-01', status='cancelled', amount=Decimal('900000'))
        staff = self.create_staff('finance_dashboard', 'FINANCE')
        self.client.force_login(staff)

        response = self.client.get(reverse('admin_panel:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['revenue'], Decimal('1200000'))
        self.assertContains(response, 'Doanh thu đã thu')
        self.assertEqual(response.context['orders_total'], 2)
        self.assertEqual(response.context['orders_cancelled'], 1)

    def test_non_finance_role_cannot_see_revenue(self):
        self.create_order('PAID-02')
        staff = self.create_staff('order_dashboard', 'ORDER')
        self.client.force_login(staff)

        response = self.client.get(reverse('admin_panel:dashboard'))

        self.assertFalse(response.context['can_view_finance'])
        self.assertNotContains(response, 'Doanh thu đã thu')
        self.assertContains(response, 'PAID-02')

    def test_product_role_sees_low_stock_but_not_order_table(self):
        staff = self.create_staff('product_dashboard', 'PRODUCT')
        self.client.force_login(staff)

        response = self.client.get(reverse('admin_panel:dashboard'))

        self.assertContains(response, 'DASH-40')
        self.assertContains(response, 'SKU tồn thấp')
        self.assertNotContains(response, 'Đơn gần đây')

    def test_date_filter_only_counts_orders_in_selected_period(self):
        self.create_order('TODAY-01')
        self.create_order('OLD-01', days_ago=60)
        staff = self.create_staff('order_filter', 'ORDER')
        self.client.force_login(staff)
        today = timezone.localdate()

        response = self.client.get(reverse('admin_panel:dashboard'), {
            'from': today.isoformat(),
            'to': today.isoformat(),
        })

        self.assertEqual(response.context['orders_total'], 1)
        self.assertContains(response, 'TODAY-01')
        self.assertNotContains(response, 'OLD-01')

    def test_invalid_date_filter_falls_back_to_last_thirty_days(self):
        staff = self.create_staff('order_invalid_filter', 'ORDER')
        self.client.force_login(staff)

        response = self.client.get(reverse('admin_panel:dashboard'), {
            'from': 'not-a-date', 'to': '2026-11-06',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ngày lọc phải có định dạng')


class AdminCatalogTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='catalog_staff', password='StrongPass123', is_staff=True)
        StaffProfile.objects.create(user=self.staff, role='PRODUCT')
        self.client.force_login(self.staff)

    def test_create_category_writes_audit(self):
        response = self.client.post(reverse('admin_panel:catalog_create', args=['category']), {
            'name':'Áo bóng đá','slug':'ao-bong-da','order':1,'is_active':'on','is_featured':'on',
        })
        self.assertRedirects(response, reverse('admin_panel:categories'))
        obj = Category.objects.get(slug='ao-bong-da')
        self.assertTrue(AuditLog.objects.filter(action='catalog.category.created', target_id=str(obj.id)).exists())

    def test_duplicate_slug_and_category_cycle_are_rejected(self):
        parent = Category.objects.create(name='Cha', slug='cha')
        child = Category.objects.create(name='Con', slug='con', parent=parent)
        duplicate = self.client.post(reverse('admin_panel:catalog_create', args=['category']), {
            'name':'Khác','slug':'cha','order':0,'is_active':'on','is_featured':'on',
        })
        cycle = self.client.post(reverse('admin_panel:catalog_edit', args=['category', parent.id]), {
            'name':'Cha','slug':'cha','parent':child.id,'order':0,'is_active':'on','is_featured':'on',
        })
        self.assertContains(duplicate, 'Slug này đã tồn tại')
        self.assertContains(cycle, 'danh mục con')

    def test_toggle_hides_without_deleting_linked_product(self):
        category = Category.objects.create(name='Có hàng', slug='co-hang')
        product = Product.objects.create(category=category, name='Áo test', slug='ao-test-admin', price=500000, image='products/test.jpg')
        self.client.post(reverse('admin_panel:catalog_toggle', args=['category', category.id]))
        category.refresh_from_db()
        self.assertFalse(category.is_active)
        self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_brand_and_sport_crud(self):
        self.client.post(reverse('admin_panel:catalog_create', args=['brand']), {'name':'Puma Admin','slug':'puma-admin','order':1,'is_active':'on'})
        self.client.post(reverse('admin_panel:catalog_create', args=['sport']), {'name':'Bóng đá','slug':'bong-da','order':1,'is_active':'on'})
        self.assertTrue(Brand.objects.filter(slug='puma-admin').exists())
        self.assertTrue(SportType.objects.filter(slug='bong-da').exists())

    def test_other_role_is_forbidden(self):
        User = get_user_model()
        user = User.objects.create_user(username='order_only', password='StrongPass123', is_staff=True)
        StaffProfile.objects.create(user=user, role='ORDER')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('admin_panel:categories')).status_code, 403)


class AdminProductTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username='product_admin', password='StrongPass123', is_staff=True)
        StaffProfile.objects.create(user=self.staff, role='PRODUCT')
        self.client.force_login(self.staff)
        self.category = Category.objects.create(name='Sản phẩm Admin', slug='san-pham-admin')

    def image(self, name='image.png'):
        content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
        return SimpleUploadedFile(name, content, content_type='image/png')

    def create_product(self, slug='admin-product'):
        return Product.objects.create(category=self.category, name='Admin Product', slug=slug, price=900000, image='products/test.jpg', status='draft', is_active=False)

    def test_create_product_starts_as_draft(self):
        response = self.client.post(reverse('admin_panel:product_create'), {
            'name':'Giày Admin','slug':'giay-admin','category':self.category.id,'price':1200000,
            'image':self.image(),'gender':'unisex','discount_percent':0,'material':'Da',
        })
        product = Product.objects.get(slug='giay-admin')
        self.assertRedirects(response, reverse('admin_panel:product_edit', args=[product.id]))
        self.assertEqual(product.status, 'draft')
        self.assertFalse(product.is_active)

    def test_publish_requires_active_variant(self):
        product = self.create_product()
        response = self.client.post(reverse('admin_panel:product_publish', args=[product.id]), follow=True)
        product.refresh_from_db()
        self.assertEqual(product.status, 'draft')
        self.assertContains(response, 'ít nhất một SKU')

    def test_publish_and_archive_product(self):
        product = self.create_product()
        ProductVariant.objects.create(product=product, sku='ADMIN-40', size='40', color='Đen', price=900000, stock=2)
        self.client.post(reverse('admin_panel:product_publish', args=[product.id]))
        product.refresh_from_db()
        self.assertTrue(product.is_active)
        self.assertEqual(product.status, 'published')
        self.client.post(reverse('admin_panel:product_archive', args=[product.id]))
        product.refresh_from_db()
        self.assertFalse(product.is_active)
        self.assertEqual(product.status, 'archived')

    def test_bulk_hide_and_csv_export(self):
        first = self.create_product('first-product')
        second = self.create_product('second-product')
        self.client.post(reverse('admin_panel:product_bulk_hide'), {'product_ids':[first.id, second.id]})
        self.assertEqual(Product.objects.filter(id__in=[first.id,second.id], status='archived').count(), 2)
        response = self.client.get(reverse('admin_panel:product_export'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertContains(response, 'Admin Product')

    def test_fake_gallery_file_is_rejected(self):
        product = self.create_product()
        fake = SimpleUploadedFile('fake.jpg', b'not-image', content_type='text/plain')
        response = self.client.post(reverse('admin_panel:product_image_add', args=[product.id]), {'image':fake}, follow=True)
        self.assertContains(response, 'không quá 5 MB')
        self.assertEqual(product.images.count(), 0)

    def test_create_variant_and_toggle(self):
        product = self.create_product()
        response = self.client.post(reverse('admin_panel:variant_add', args=[product.id]), {
            'sku':'SKU-NEW-40','barcode':'89300001','size':'40','color':'Đen',
            'price':950000,'stock':5,'is_active':'on',
        })
        self.assertRedirects(response, reverse('admin_panel:variants', args=[product.id]))
        variant = product.variants.get(sku='SKU-NEW-40')
        self.client.post(reverse('admin_panel:variant_toggle', args=[product.id, variant.id]))
        variant.refresh_from_db()
        self.assertFalse(variant.is_active)

    def test_duplicate_sku_is_rejected(self):
        product = self.create_product()
        ProductVariant.objects.create(product=product, sku='DUP-SKU', size='40', color='Đen', price=900000)
        response = self.client.post(reverse('admin_panel:variant_add', args=[product.id]), {
            'sku':'DUP-SKU','size':'41','color':'Trắng','price':900000,'stock':1,'is_active':'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductVariant.objects.filter(sku='DUP-SKU').count(), 1)

    def test_sale_price_and_time_are_validated(self):
        product = self.create_product()
        response = self.client.post(reverse('admin_panel:variant_add', args=[product.id]), {
            'sku':'SALE-BAD','size':'42','color':'Xanh','price':900000,'sale_price':1000000,
            'sale_starts_at':'2026-12-02T10:00','sale_ends_at':'2026-12-01T10:00','stock':1,'is_active':'on',
        })
        self.assertContains(response, 'Giá khuyến mãi')
        self.assertContains(response, 'Thời gian kết thúc')
        self.assertFalse(ProductVariant.objects.filter(sku='SALE-BAD').exists())


class AdminOrderOperationTests(TestCase):
    def setUp(self):
        User=get_user_model(); self.staff=User.objects.create_user(username='order_admin',password='StrongPass123',is_staff=True); StaffProfile.objects.create(user=self.staff,role='ORDER'); self.client.force_login(self.staff)
        self.customer=Customer.objects.create(username='Buyer',email='buyer@ex.com',phone='0912345678',password='x')
        category=Category.objects.create(name='Order Admin Cat',slug='order-admin-cat'); product=Product.objects.create(category=category,name='Order Admin Product',slug='order-admin-product',price=500000,image='products/test.jpg')
        self.variant=ProductVariant.objects.create(product=product,sku='ORDER-40',size='40',color='Đen',price=500000,stock=10)
        self.order=Order.objects.create(user=self.customer,order_code='ADMIN-ORDER',idempotency_key='admin-order-key',payment_method='cod',shipping_method='standard',subtotal=500000,shipping_fee=0,grand_total=500000)
        OrderItem.objects.create(order=self.order,variant=self.variant,product_name=product.name,sku=self.variant.sku,size='40',color='Đen',unit_price=500000,quantity=2,line_total=1000000)
        self.warehouse=Warehouse.objects.create(name='Kho đơn',code='ORDER-WH'); self.stock=Stock.objects.create(warehouse=self.warehouse,variant=self.variant,on_hand=5)

    def action(self,name,**data): return self.client.post(reverse('admin_panel:order_action',args=[self.order.id,name]),data)

    def test_confirm_pack_ship_flow_and_no_double_deduction(self):
        self.action('confirm'); self.action('pack',warehouse_id=self.warehouse.id); self.action('pack',warehouse_id=self.warehouse.id)
        self.stock.refresh_from_db(); self.order.refresh_from_db(); self.assertEqual(self.stock.on_hand,3); self.assertEqual(self.order.status,'packing')
        self.action('ship'); self.order.refresh_from_db(); self.assertEqual(self.order.status,'shipped')

    def test_cancel_packed_order_restores_once(self):
        self.action('confirm'); self.action('pack',warehouse_id=self.warehouse.id); self.action('cancel',note='Khách đổi ý'); self.action('cancel',note='Lặp')
        self.stock.refresh_from_db(); self.order.refresh_from_db(); self.assertEqual(self.stock.on_hand,5); self.assertEqual(self.order.status,'cancelled')

    def test_invalid_state_jump_is_rejected(self):
        self.action('ship'); self.order.refresh_from_db(); self.assertEqual(self.order.status,'pending')

