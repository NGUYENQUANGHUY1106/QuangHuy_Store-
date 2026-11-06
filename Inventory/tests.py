from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from AdminPanel.models import StaffProfile
from Product.models import Category,Product,ProductVariant
from .models import Stock,StockCount,StockCountItem,StockMovement,Warehouse
from .services import adjust_stock


class InventoryTests(TestCase):
    def setUp(self):
        User=get_user_model(); self.staff=User.objects.create_user(username='warehouse',password='StrongPass123',is_staff=True); StaffProfile.objects.create(user=self.staff,role='WAREHOUSE')
        category=Category.objects.create(name='Kho test',slug='kho-test'); product=Product.objects.create(category=category,name='Kho Product',slug='kho-product',price=500000,image='products/test.jpg')
        self.variant=ProductVariant.objects.create(product=product,sku='KHO-40',size='40',color='Đen',price=500000,stock=10)
        self.warehouse=Warehouse.objects.create(name='Kho chính',code='MAIN'); self.stock=Stock.objects.create(warehouse=self.warehouse,variant=self.variant,on_hand=10,reserved=2,reorder_point=3)
        self.client.force_login(self.staff)

    def test_adjust_stock_locks_updates_and_logs(self):
        adjust_stock(self.stock.id,12,'Kiểm kê',self.staff)
        self.stock.refresh_from_db(); self.variant.refresh_from_db()
        self.assertEqual(self.stock.on_hand,12); self.assertEqual(self.variant.stock,10)
        self.assertTrue(StockMovement.objects.filter(stock=self.stock,quantity=2).exists())

    def test_cannot_adjust_below_reserved(self):
        with self.assertRaises(ValidationError): adjust_stock(self.stock.id,1,'Sai',self.staff)

    def test_count_completion_adjusts_once(self):
        count=StockCount.objects.create(warehouse=self.warehouse,created_by=self.staff)
        StockCountItem.objects.create(stock_count=count,stock=self.stock,system_quantity=10,counted_quantity=8)
        response=self.client.post(reverse('inventory:count_complete',args=[count.id]))
        self.assertRedirects(response,reverse('inventory:stock_list')); self.stock.refresh_from_db(); count.refresh_from_db()
        self.assertEqual(self.stock.on_hand,8); self.assertEqual(count.status,'completed')
        self.assertEqual(self.client.post(reverse('inventory:count_complete',args=[count.id])).status_code,404)

    def test_other_role_is_forbidden(self):
        User=get_user_model(); user=User.objects.create_user(username='support_inventory',password='x',is_staff=True); StaffProfile.objects.create(user=user,role='SUPPORT'); self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('inventory:stock_list')).status_code,403)

    def test_unique_stock_per_warehouse_and_variant(self):
        with self.assertRaises(IntegrityError): Stock.objects.create(warehouse=self.warehouse,variant=self.variant,on_hand=1)
