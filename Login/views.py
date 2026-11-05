import hashlib
import re
import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import PasswordResetToken, User


def password_is_strong(password):
    return len(password) >= 8 and re.search(r'[A-Za-z]', password) and re.search(r'\d', password)


def current_user(request):
    user_id = request.session.get('user_id')
    return User.objects.filter(id=user_id).first() if user_id else None


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

        if not password_is_strong(password):
            context['error'] = 'Mật khẩu phải có ít nhất 8 ký tự, gồm chữ và số.'
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

        if User.objects.filter(username__iexact=full_name).exists():
            context['error'] = 'Tên tài khoản này đã được sử dụng.'
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
    next_url = request.GET.get('next', request.POST.get('next', ''))
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

        now = int(timezone.now().timestamp())
        attempts = [item for item in request.session.get('login_attempts', []) if now - item < 300]
        if len(attempts) >= 10:
            return render(request, 'Login.html', {
                'error': 'Bạn đã thử quá nhiều lần. Vui lòng đợi 5 phút.',
                'email': email,
                'next': next_url,
            }, status=429)

        user = User.objects.filter(email__iexact=email).first()

        if user is None or not check_password(password, user.password):
            attempts.append(now)
            request.session['login_attempts'] = attempts
            return render(
                request,
                'Login.html',
                {'error': 'Email hoặc mật khẩu không chính xác.', 'email': email, 'next': next_url},
            )

        request.session.cycle_key()
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['email'] = user.email
        request.session.pop('login_attempts', None)

        if remember:
            request.session.set_expiry(30 * 24 * 60 * 60)
        else:
            request.session.set_expiry(0)

        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('home')

    return render(request, 'Login.html', {'next': next_url})


@require_POST
def logout_page(request):
    cart = request.session.get('cart', {})
    cart_count = request.session.get('cart_count', 0)
    request.session.flush()
    if cart:
        request.session['cart'] = cart
        request.session['cart_count'] = cart_count
    messages.success(request, 'Bạn đã đăng xuất thành công.')
    return redirect('home')


def account_page(request):
    user = current_user(request)
    if user is None:
        return redirect(f"{reverse('login')}?next={request.path}")
    return render(request, 'Account.html', {'account_user': user})


def forgot_password_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            raw_token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(
                user=user,
                token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                expires_at=timezone.now() + timedelta(minutes=30),
            )
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[raw_token]))
            send_mail(
                'Đặt lại mật khẩu QuangHuy Store',
                f'Mở liên kết sau trong vòng 30 phút: {reset_url}',
                'no-reply@quanghuystore.local',
                [user.email],
            )
        messages.success(request, 'Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi.')
        return redirect('forgot_password')
    return render(request, 'ForgotPassword.html')


def reset_password_page(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset_token = PasswordResetToken.objects.select_related('user').filter(token_hash=token_hash).first()
    token_valid = (
        reset_token is not None
        and reset_token.used_at is None
        and reset_token.expires_at > timezone.now()
    )

    if request.method == 'POST':
        if not token_valid:
            return render(request, 'ResetPassword.html', {'token_valid': False})
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if not password_is_strong(password):
            return render(request, 'ResetPassword.html', {
                'token_valid': True,
                'error': 'Mật khẩu phải có ít nhất 8 ký tự, gồm chữ và số.',
            })
        if password != confirm_password:
            return render(request, 'ResetPassword.html', {
                'token_valid': True,
                'error': 'Mật khẩu nhập lại không khớp.',
            })

        with transaction.atomic():
            locked_token = PasswordResetToken.objects.select_for_update().select_related('user').get(pk=reset_token.pk)
            if locked_token.used_at is not None or locked_token.expires_at <= timezone.now():
                return render(request, 'ResetPassword.html', {'token_valid': False})
            locked_token.user.password = make_password(password)
            locked_token.user.save(update_fields=['password'])
            locked_token.used_at = timezone.now()
            locked_token.save(update_fields=['used_at'])
        messages.success(request, 'Đặt lại mật khẩu thành công. Bạn có thể đăng nhập.')
        return redirect('login')

    return render(request, 'ResetPassword.html', {'token_valid': token_valid})
