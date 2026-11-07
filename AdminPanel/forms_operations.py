from django import forms
from django.contrib.auth import get_user_model

from Checkout.models import Coupon, Promotion
from Product.models import Banner
from Support.models import BlogPost, FAQ, SiteSettings, StaticPage

from .models import StaffProfile


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percent', 'discount_amount', 'max_discount', 'min_order',
                  'usage_limit', 'per_user_limit', 'starts_at', 'ends_at', 'is_active']
        widgets = {'starts_at': DateTimeInput(), 'ends_at': DateTimeInput()}

    def clean(self):
        data = super().clean()
        if not data.get('discount_percent') and not data.get('discount_amount'):
            self.add_error('discount_percent', 'Cần nhập phần trăm hoặc số tiền giảm.')
        if data.get('starts_at') and data.get('ends_at') and data['starts_at'] >= data['ends_at']:
            self.add_error('ends_at', 'Ngày kết thúc phải sau ngày bắt đầu.')
        return data


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['title', 'description', 'discount_percent', 'products', 'categories',
                  'starts_at', 'ends_at', 'is_active']
        widgets = {'starts_at': DateTimeInput(), 'ends_at': DateTimeInput(),
                   'products': forms.CheckboxSelectMultiple(), 'categories': forms.CheckboxSelectMultiple()}


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'subtitle', 'image', 'link_text', 'link_url', 'order',
                  'starts_at', 'ends_at', 'is_active']
        widgets = {'starts_at': DateTimeInput(), 'ends_at': DateTimeInput()}


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'slug', 'summary', 'content', 'meta_description', 'status', 'published_at']
        widgets = {'published_at': DateTimeInput()}


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer', 'order', 'is_active']


class StaticPageForm(forms.ModelForm):
    class Meta:
        model = StaticPage
        fields = ['title', 'slug', 'content', 'meta_description', 'is_active']


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['store_name', 'contact_email', 'hotline', 'address', 'shipping_fee',
                  'free_shipping_min', 'low_stock_threshold', 'allow_checkout']


class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    role = forms.ChoiceField(choices=StaffProfile.ROLE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput, required=False,
                               help_text='Chỉ nhập khi tạo mới hoặc muốn đổi mật khẩu.')
    is_active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields['username'].initial = instance.username
            self.fields['email'].initial = instance.email
            self.fields['is_active'].initial = instance.is_active
            self.fields['role'].initial = getattr(getattr(instance, 'staff_profile', None), 'role', '')

    def clean_username(self):
        value = self.cleaned_data['username']
        users = get_user_model().objects.filter(username=value)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise forms.ValidationError('Tên đăng nhập đã tồn tại.')
        return value
