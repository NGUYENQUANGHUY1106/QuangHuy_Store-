from django import forms
from .models import PurchaseOrder,PurchaseOrderItem,Stock,StockCount,Supplier,Warehouse


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


class SupplierForm(forms.ModelForm):
    class Meta: model=Supplier; fields=['name','code','phone','email','address','is_active']


class PurchaseOrderForm(forms.ModelForm):
    class Meta: model=PurchaseOrder; fields=['supplier','code','note']


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta: model=PurchaseOrderItem; fields=['variant','quantity','unit_cost']
