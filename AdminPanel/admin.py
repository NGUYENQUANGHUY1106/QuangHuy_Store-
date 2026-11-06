from django.contrib import admin

from .models import AuditLog, StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'updated_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'target_type', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('actor__username', 'description', 'target_id')
    readonly_fields = ('actor', 'action', 'target_type', 'target_id', 'description', 'ip_address', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

