from django.db import models

# Create your models here.

class User(models.Model) :
    username  = models.CharField(max_length=200, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10)
    avatar = models.FileField(blank=True)
    password = models.CharField(max_length=200)

    class Meta :
        db_table = 'user'


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_token'
        ordering = ['-created_at']


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=10)
    province = models.CharField(max_length=100)
    ward = models.CharField(max_length=100)
    detail = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    is_used_in_order = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'address'
        ordering = ['-is_default', '-created_at']
