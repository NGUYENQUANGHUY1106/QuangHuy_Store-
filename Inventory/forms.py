from django import forms
from .models import Stock, StockCount, Warehouse


class WarehouseForm(forms.ModelForm):
    class Meta:
        model=Warehouse; fields=['name','code','address','is_online','is_active']


class StockForm(forms.ModelForm):
    class Meta:
        model=Stock; fields=['warehouse','variant','on_hand','reserved','reorder_point']

    def clean(self):
        data=super().clean()
        if data.get('on_hand',0)<data.get('reserved',0): self.add_error('reserved','Số giữ không được vượt tồn thực tế.')
        return data


class StockCountForm(forms.ModelForm):
    class Meta:
        model=StockCount; fields=['warehouse','note']
