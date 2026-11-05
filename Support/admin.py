from django.contrib import admin
from .models import FAQ,Notification,SiteSettings,StaticPage,SupportMessage,SupportTicket
admin.site.register(FAQ);admin.site.register(Notification);admin.site.register(SupportMessage);admin.site.register(SupportTicket)
admin.site.register(StaticPage);admin.site.register(SiteSettings)
