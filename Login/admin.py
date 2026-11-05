from django.contrib import admin

from .models import Address, PasswordResetToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone')
    search_fields = ('username', 'email', 'phone')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'used_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token_hash', 'created_at')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'user', 'phone', 'province', 'ward', 'is_default')
    list_filter = ('province', 'is_default')
    search_fields = ('recipient_name', 'phone', 'user__email')
