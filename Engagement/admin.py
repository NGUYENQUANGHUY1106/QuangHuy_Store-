from django.contrib import admin
from .models import RecentlyViewed, WishlistItem

admin.site.register(WishlistItem)
admin.site.register(RecentlyViewed)
