from datetime import date
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from Checkout.models import Order
from AdminPanel.models import StaffProfile
from Login.models import Address,User
from .models import Shipment,ShipmentEvent,ShippingMethod,ShippingZone
from .services import shipping_options_for

class ShippingTests(TestCase):
    def setUp(self):
        self.user=User.objects.create(username='Ship User',email='ship@example.com',phone='0912345678',password=make_password('secret123'))
        self.address=Address.objects.create(user=self.user,recipient_name='A',phone='0912345678',province='Da Nang',ward='Hai Chau',detail='12 Tran Phu')
        session=self.client.session;session['user_id']=self.user.id;session.save()
    def test_default_shipping_and_free_threshold(self):
        low=shipping_options_for(self.address,Decimal('500000'));high=shipping_options_for(self.address,Decimal('1000000'))
        self.assertEqual(next(x for x in low if x['code']=='standard')['fee'],30000)
        self.assertEqual(next(x for x in high if x['code']=='standard')['fee'],0)
    def test_address_outside_configured_zone_is_not_available(self):
        method=ShippingMethod.objects.create(code='local',name='Nội thành',base_fee=20000)
        ShippingZone.objects.create(method=method,province='Ha Noi',surcharge=0)
        self.assertEqual(shipping_options_for(self.address,Decimal('100000')),[])
    def test_tracking_is_private_and_event_id_is_unique(self):
        order=Order.objects.create(user=self.user,order_code='QHSHIP01',idempotency_key='ship-key',payment_method='cod',shipping_method='standard',subtotal=100,shipping_fee=0,grand_total=100)
        shipment=Shipment.objects.create(order=order,carrier='GHN',tracking_code='TRACK01',status='shipping',estimated_delivery=date.today())
        ShipmentEvent.objects.create(shipment=shipment,event_id='EVENT01',status='shipping',description='Đang giao',occurred_at=timezone.now())
        self.assertEqual(self.client.get(reverse('shipment_status',args=[order.order_code])).json()['tracking_code'],'TRACK01')
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): ShipmentEvent.objects.create(shipment=shipment,event_id='EVENT01',status='shipping',description='Trùng',occurred_at=timezone.now())
        other=User.objects.create(username='Other Ship',email='other-ship@example.com',phone='0987654321',password=make_password('secret123'))
        session=self.client.session;session['user_id']=other.id;session.save()
        self.assertEqual(self.client.get(reverse('shipment_status',args=[order.order_code])).status_code,404)


class AdminShippingTests(TestCase):
    def setUp(self):
        UserAuth=get_user_model();self.staff=UserAuth.objects.create_user(username='ship_staff',password='StrongPass123',is_staff=True);StaffProfile.objects.create(user=self.staff,role='ORDER');self.client.force_login(self.staff)
        self.user=User.objects.create(username='Ship Buyer',email='ship-buyer@example.com',phone='0912345678',password='x')
        self.order=Order.objects.create(user=self.user,order_code='ADMINSHIP',idempotency_key='admin-ship',status='packing',payment_method='cod',shipping_method='standard',subtotal=100,shipping_fee=0,grand_total=100)
        self.shipment=Shipment.objects.create(order=self.order,carrier='GHN',tracking_code='ADMIN-TRACK')

    def event(self,event_id,status): return self.client.post(reverse('shipping_admin:add_event',args=[self.shipment.id]),{'event_id':event_id,'status':status,'description':status})

    def test_valid_events_update_shipment_and_order(self):
        self.event('E1','picked');self.event('E2','shipping');self.shipment.refresh_from_db();self.order.refresh_from_db()
        self.assertEqual(self.shipment.status,'shipping');self.assertEqual(self.order.status,'shipping')

    def test_event_replay_and_invalid_transition_do_not_duplicate(self):
        self.event('E1','picked');self.event('E1','shipping');self.event('BAD','delivered')
        self.shipment.refresh_from_db();self.assertEqual(self.shipment.status,'picked');self.assertEqual(ShipmentEvent.objects.count(),1)

    def test_failed_can_retry_or_return(self):
        self.event('E1','picked');self.event('E2','shipping');self.event('E3','failed');self.event('E4','returned')
        self.shipment.refresh_from_db();self.assertEqual(self.shipment.status,'returned')
