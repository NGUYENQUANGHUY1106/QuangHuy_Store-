from django import forms

from Product.models import Brand, Category, SportType


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
