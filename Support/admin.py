from django.contrib import admin
from .models import FAQ,Notification,SupportMessage,SupportTicket
admin.site.register(FAQ);admin.site.register(Notification);admin.site.register(SupportMessage);admin.site.register(SupportTicket)
