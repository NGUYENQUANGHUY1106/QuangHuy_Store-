from django.contrib import admin
from .models import ReturnRequest,ReturnItem,ReturnEvidence,Refund
admin.site.register(ReturnRequest);admin.site.register(ReturnItem);admin.site.register(ReturnEvidence);admin.site.register(Refund)
