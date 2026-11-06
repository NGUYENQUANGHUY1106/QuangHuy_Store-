from django import forms

from Product.models import Brand, Category, Product, ProductVariant, SportType


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'parent', 'description', 'logo', 'order', 'is_active', 'is_featured']
        labels = {'name':'Tên danh mục','parent':'Danh mục cha','description':'Mô tả','logo':'Logo','order':'Thứ tự','is_active':'Đang hiển thị','is_featured':'Nổi bật'}
        error_messages = {'slug': {'unique': 'Slug này đã tồn tại.'}, 'name': {'unique': 'Tên danh mục đã tồn tại.'}}

    def clean_parent(self):
        parent = self.cleaned_data.get('parent')
        if not parent or not self.instance.pk:
            return parent
        current = parent
        while current:
            if current.pk == self.instance.pk:
                raise forms.ValidationError('Không thể chọn chính nó hoặc danh mục con làm danh mục cha.')
            current = current.parent
        return parent


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'logo', 'order', 'is_active']
        labels = {'name':'Tên thương hiệu','logo':'Logo','order':'Thứ tự','is_active':'Đang hiển thị'}
        error_messages = {'slug': {'unique': 'Slug này đã tồn tại.'}, 'name': {'unique': 'Tên thương hiệu đã tồn tại.'}}


class SportTypeForm(forms.ModelForm):
    class Meta:
        model = SportType
        fields = ['name', 'slug', 'description', 'order', 'is_active']
        labels = {'name':'Tên môn thể thao','description':'Mô tả','order':'Thứ tự','is_active':'Đang hiển thị'}
        error_messages = {'slug': {'unique': 'Slug này đã tồn tại.'}, 'name': {'unique': 'Tên môn thể thao đã tồn tại.'}}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','slug','category','brand','sport_type','price','image','description','material','size_guide','gender','is_new','is_best_seller','discount_percent','seo_title','meta_description']
        labels = {'name':'Tên sản phẩm','category':'Danh mục','brand':'Thương hiệu','sport_type':'Môn thể thao','price':'Giá','image':'Ảnh chính','description':'Mô tả','material':'Chất liệu','size_guide':'Hướng dẫn size','gender':'Giới tính','is_new':'Hàng mới','is_best_seller':'Bán chạy','discount_percent':'Giảm giá (%)','seo_title':'Tiêu đề SEO','meta_description':'Mô tả SEO'}
        error_messages = {'slug': {'unique':'Slug này đã tồn tại.'}}

    def clean_price(self):
        value = self.cleaned_data['price']
        if value < 0:
            raise forms.ValidationError('Giá không được âm.')
        return value


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['sku','barcode','size','color','price','sale_price','sale_starts_at','sale_ends_at','image','stock','is_active']
        labels = {'sku':'Mã SKU','barcode':'Barcode','size':'Size','color':'Màu','price':'Giá bán','sale_price':'Giá khuyến mãi','sale_starts_at':'Bắt đầu giảm giá','sale_ends_at':'Kết thúc giảm giá','image':'Ảnh biến thể','stock':'Tồn hiện tại','is_active':'Đang bán'}
        widgets = {'sale_starts_at': forms.DateTimeInput(attrs={'type':'datetime-local'}), 'sale_ends_at': forms.DateTimeInput(attrs={'type':'datetime-local'})}

    def clean(self):
        cleaned = super().clean()
        price = cleaned.get('price'); sale = cleaned.get('sale_price')
        if price is not None and price < 0: self.add_error('price', 'Giá không được âm.')
        if sale is not None and (sale < 0 or (price is not None and sale > price)): self.add_error('sale_price', 'Giá khuyến mãi phải từ 0 đến giá bán.')
        start = cleaned.get('sale_starts_at'); end = cleaned.get('sale_ends_at')
        if start and end and start >= end: self.add_error('sale_ends_at', 'Thời gian kết thúc phải sau thời gian bắt đầu.')
        return cleaned
