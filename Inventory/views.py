from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from AdminPanel.permissions import admin_permission_required
from AdminPanel.services import menu_for_user, write_audit
from .forms import PurchaseOrderForm,PurchaseOrderItemForm,StockCountForm,StockForm,SupplierForm,WarehouseForm
from .models import PurchaseOrder,PurchaseOrderItem,Stock,StockCount,StockCountItem,StockMovement,Supplier,Warehouse
from .services import adjust_stock,receive_purchase_item


def context(request, **extra):
    data={'admin_menu':menu_for_user(request.user)}; data.update(extra); return data


@admin_permission_required('inventory.view')
def stock_list(request):
    stocks=Stock.objects.select_related('warehouse','variant__product')
    if request.GET.get('low')=='1': stocks=stocks.filter(on_hand__lte=F('reorder_point'))
    warehouse=request.GET.get('warehouse')
    if warehouse: stocks=stocks.filter(warehouse_id=warehouse)
    return render(request,'Inventory/StockList.html',context(request,stocks=stocks,warehouses=Warehouse.objects.all(),movements=StockMovement.objects.select_related('stock__variant','actor')[:20]))


@admin_permission_required('inventory.adjust')
@require_http_methods(['GET','POST'])
def warehouse_create(request):
    form=WarehouseForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(); write_audit(request,'warehouse.created',obj.code,'warehouse',obj.id); return redirect('inventory:stock_list')
    return render(request,'Inventory/Form.html',context(request,form=form,title='Thêm kho'))


@admin_permission_required('inventory.adjust')
@require_http_methods(['GET','POST'])
def stock_create(request):
    form=StockForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        stock=form.save(); adjust_stock(stock.id,stock.on_hand,'Khởi tạo tồn kho',request.user); return redirect('inventory:stock_list')
    return render(request,'Inventory/Form.html',context(request,form=form,title='Tạo tồn SKU'))


@admin_permission_required('inventory.adjust')
@require_POST
def stock_adjust(request, stock_id):
    try:
        quantity=int(request.POST.get('quantity','-1')); reason=request.POST.get('reason','').strip()
        if not reason: raise ValueError
        adjust_stock(stock_id,quantity,reason,request.user)
        write_audit(request,'stock.adjusted',reason,'stock',stock_id); messages.success(request,'Đã điều chỉnh tồn kho.')
    except (ValueError,ValidationError) as error: messages.error(request,str(error) or 'Dữ liệu không hợp lệ.')
    return redirect('inventory:stock_list')


@admin_permission_required('inventory.adjust')
@require_http_methods(['GET','POST'])
def count_create(request):
    form=StockCountForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        count=form.save(commit=False); count.created_by=request.user; count.save()
        for stock in count.warehouse.stocks.all():
            raw=request.POST.get(f'stock_{stock.id}')
            if raw is not None: StockCountItem.objects.create(stock_count=count,stock=stock,system_quantity=stock.on_hand,counted_quantity=max(0,int(raw)))
        return redirect('inventory:count_complete',count.id)
    return render(request,'Inventory/CountForm.html',context(request,form=form,warehouses=Warehouse.objects.prefetch_related('stocks__variant')))


@admin_permission_required('inventory.adjust')
@require_POST
@transaction.atomic
def count_complete(request, count_id):
    count=StockCount.objects.select_for_update().filter(pk=count_id,status='draft').first()
    if not count: raise Http404
    for item in count.items.select_related('stock'):
        adjust_stock(item.stock_id,item.counted_quantity,f'Kiểm kê #{count.id}',request.user,str(count.id))
    from django.utils import timezone
    count.status='completed'; count.completed_at=timezone.now(); count.save(update_fields=['status','completed_at'])
    write_audit(request,'stock_count.completed',f'Kiểm kê #{count.id}','stock_count',count.id)
    return redirect('inventory:stock_list')


@admin_permission_required('suppliers.view')
def procurement(request):
    return render(request,'Inventory/Procurement.html',context(request,suppliers=Supplier.objects.all(),orders=PurchaseOrder.objects.prefetch_related('items__variant').select_related('supplier'),warehouses=Warehouse.objects.filter(is_active=True)))


@admin_permission_required('suppliers.change')
@require_http_methods(['GET','POST'])
def supplier_create(request):
    form=SupplierForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(); write_audit(request,'supplier.created',obj.code,'supplier',obj.id); return redirect('inventory:procurement')
    return render(request,'Inventory/Form.html',context(request,form=form,title='Thêm nhà cung cấp'))


@admin_permission_required('suppliers.change')
@require_http_methods(['GET','POST'])
def po_create(request):
    form=PurchaseOrderForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False); obj.created_by=request.user; obj.save(); return redirect('inventory:po_item_add',obj.id)
    return render(request,'Inventory/Form.html',context(request,form=form,title='Tạo phiếu mua'))


@admin_permission_required('suppliers.change')
@require_http_methods(['GET','POST'])
def po_item_add(request, po_id):
    order=PurchaseOrder.objects.filter(pk=po_id,status='draft').first()
    if not order: raise Http404
    form=PurchaseOrderItemForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False); item.purchase_order=order; item.save(); return redirect('inventory:procurement')
    return render(request,'Inventory/Form.html',context(request,form=form,title=f'Thêm SKU vào {order.code}'))


@admin_permission_required('suppliers.change')
@require_POST
def po_approve(request, po_id):
    order=PurchaseOrder.objects.filter(pk=po_id,status='draft').first()
    if not order or not order.items.exists(): raise Http404
    order.status='approved'; order.save(update_fields=['status']); write_audit(request,'purchase_order.approved',order.code,'purchase_order',order.id)
    return redirect('inventory:procurement')


@admin_permission_required('suppliers.change')
@require_POST
def receive_item(request, item_id):
    try:
        warehouse=Warehouse.objects.get(pk=request.POST.get('warehouse_id'))
        receipt,created=receive_purchase_item(item_id,warehouse,int(request.POST.get('quantity','0')),request.POST.get('receipt_code','').strip(),request.user)
        messages.success(request,'Đã nhập kho.' if created else 'Mã phiếu này đã được xử lý trước đó.')
    except (ValueError,ValidationError,Warehouse.DoesNotExist) as error: messages.error(request,str(error))
    return redirect('inventory:procurement')
