import re

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from .models import User


def home_page(request):
    return render(request, 'Home.html')


def register_page(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        avatar = request.FILES.get('avatar')

        context = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
        }

        if not all([full_name, email, phone, password, confirm_password, avatar]):
            context['error'] = 'Vui lòng nhập đầy đủ thông tin.'
            return render(request, 'Register.html', context)

        try:
            validate_email(email)
        except ValidationError:
            context['error'] = 'Địa chỉ email không hợp lệ.'
            return render(request, 'Register.html', context)

        if not re.fullmatch(r'0\d{9}', phone):
            context['error'] = 'Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0.'
            return render(request, 'Register.html', context)

        if len(password) < 6:
            context['error'] = 'Mật khẩu phải có ít nhất 6 ký tự.'
            return render(request, 'Register.html', context)

        if password != confirm_password:
            context['error'] = 'Mật khẩu nhập lại không khớp.'
            return render(request, 'Register.html', context)

        if not getattr(avatar, 'content_type', '').startswith('image/'):
            context['error'] = 'Avatar phải là một tệp hình ảnh.'
            return render(request, 'Register.html', context)

        if avatar.size > 5 * 1024 * 1024:
            context['error'] = 'Kích thước avatar không được vượt quá 5 MB.'
            return render(request, 'Register.html', context)

        if User.objects.filter(email__iexact=email).exists():
            context['error'] = 'Email này đã được đăng ký.'
            return render(request, 'Register.html', context)

        try:
            with transaction.atomic():
                User.objects.create(
                    username=full_name,
                    email=email,
                    phone=phone,
                    avatar=avatar,
                    password=make_password(password),
                )
        except IntegrityError:
            context['error'] = 'Email này đã được đăng ký.'
            return render(request, 'Register.html', context)

        messages.success(request, 'Đăng ký thành công. Bạn có thể đăng nhập ngay bây giờ.')
        return redirect('login')

    return render(request, 'Register.html')


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember') == 'on'

        if not email or not password:
            return render(
                request,
                'Login.html',
                {'error': 'Vui lòng nhập email và mật khẩu.', 'email': email},
            )

        user = User.objects.filter(email__iexact=email).first()

        if user is None or not check_password(password, user.password):
            return render(
                request,
                'Login.html',
                {'error': 'Email hoặc mật khẩu không chính xác.', 'email': email},
            )

        request.session.cycle_key()
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['email'] = user.email

        if remember:
            request.session.set_expiry(30 * 24 * 60 * 60)
        else:
            request.session.set_expiry(0)

        return redirect('home')

    return render(request, 'Login.html')
