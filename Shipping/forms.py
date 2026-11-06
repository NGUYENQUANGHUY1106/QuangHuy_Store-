from django import forms
from .models import Shipment,ShippingMethod,ShippingZone
class ShippingMethodForm(forms.ModelForm):
    class Meta: model=ShippingMethod; fields='__all__'
class ShippingZoneForm(forms.ModelForm):
    class Meta: model=ShippingZone; fields='__all__'
class ShipmentForm(forms.ModelForm):
    class Meta: model=Shipment; fields=['order','carrier','tracking_code','tracking_url','estimated_delivery','actual_fee','cod_collected']
    def clean_order(self):
        order=self.cleaned_data['order']
        if order.status not in ['packing','shipped']: raise forms.ValidationError('Chỉ tạo vận đơn sau khi đóng gói.')
        return order
