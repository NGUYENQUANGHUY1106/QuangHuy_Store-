from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction

from AdminPanel.models import StaffProfile


class Command(BaseCommand):
    help = 'Tạo tài khoản nhân viên và gán vai trò cho AdminPanel.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--role', required=True, choices=[item[0] for item in StaffProfile.ROLE_CHOICES])

    def handle(self, *args, **options):
        username = options['username'].strip()
        email = options['email'].strip().lower()
        try:
            validate_email(email)
        except ValidationError as error:
            raise CommandError('Email không hợp lệ.') from error

        password = getpass('Mật khẩu nhân viên: ')
        confirm_password = getpass('Nhập lại mật khẩu: ')
        if len(password) < 8:
            raise CommandError('Mật khẩu phải có ít nhất 8 ký tự.')
        if password != confirm_password:
            raise CommandError('Mật khẩu nhập lại không khớp.')

        User = get_user_model()
        if User.objects.filter(username__iexact=username).exists():
            raise CommandError('Tên đăng nhập đã tồn tại.')
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError('Email đã tồn tại.')

        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
            )
            StaffProfile.objects.create(user=user, role=options['role'])

        self.stdout.write(self.style.SUCCESS(f'Đã tạo nhân viên {username} với vai trò {options["role"]}.'))

