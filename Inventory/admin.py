from django.contrib import admin
from .models import Warehouse,Stock,StockMovement,StockCount,StockCountItem
admin.site.register([Warehouse,Stock,StockMovement,StockCount,StockCountItem])
