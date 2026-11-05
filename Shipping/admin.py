from django.contrib import admin
from .models import ShippingMethod,ShippingZone,Shipment,ShipmentEvent
admin.site.register(ShippingMethod);admin.site.register(ShippingZone);admin.site.register(Shipment);admin.site.register(ShipmentEvent)
