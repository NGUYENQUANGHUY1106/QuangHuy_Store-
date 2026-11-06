from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('PRODUCT', 'Sản phẩm'),
        ('WAREHOUSE', 'Kho hàng'),
        ('ORDER', 'Đơn hàng'),
        ('SUPPORT', 'Chăm sóc khách hàng'),
        ('MARKETING', 'Marketing'),
        ('FINANCE', 'Tài chính'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'admin_staff_profile'

    def clean(self):
        if self.user_id and not self.user.is_staff:
            raise ValidationError('Tài khoản nhân viên phải được bật quyền is_staff.')

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_audit_logs',
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_audit_log'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.action} - {self.created_at:%d/%m/%Y %H:%M}'

