# QuangHuy Store

Website bán giày và quần áo bóng đá bằng Django + PostgreSQL. U01 đã có trang chủ, menu danh mục lấy từ database, tìm kiếm, phân trang, trang chi tiết sản phẩm, banner theo lịch và các trạng thái rỗng/lỗi ảnh.

## 1. Cài đặt

Mở PowerShell tại thư mục có `manage.py` rồi chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Cấu hình PostgreSQL

Tạo database `QuangHuy_Store`. Dự án đọc thông tin kết nối từ biến môi trường để không lưu mật khẩu lên GitHub:

```powershell
$env:DB_NAME = "QuangHuy_Store"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "MAT_KHAU_POSTGRES_CUA_BAN"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
```

Các biến mẫu nằm trong `.env.example`. Cần khai báo lại biến môi trường khi mở cửa sổ PowerShell mới.

## 3. Tạo bảng và nạp dữ liệu U01

```powershell
python manage.py migrate
python manage.py seed_products
```

Muốn tải lại toàn bộ ảnh sản phẩm:

```powershell
python manage.py seed_products --refresh-images
```

Lệnh seed tạo/cập nhật:

- 4 danh mục: giày bóng đá, áo quần câu lạc bộ, áo đội tuyển quốc gia, quần bóng đá.
- 3 thương hiệu: Nike, adidas, Puma.
- 50 sản phẩm có tên tiếng Việt, giá, ảnh, nguồn ảnh và trạng thái mới/bán chạy/khuyến mãi.
- Banner trang chủ có thể bật/tắt và đặt thời gian hiển thị.

Mã nạp dữ liệu nằm tại `Product/management/commands/seed_products.py`. Ảnh được tải về `media/products`, banner nằm trong `media/banners`; vì vậy website không phụ thuộc ảnh nóng từ trang ngoài khi hiển thị.

## 4. Chạy dự án

```powershell
python manage.py runserver
```

Mở `http://127.0.0.1:8000/`.

| URL | Chức năng |
|---|---|
| `/` | Trang chủ và danh sách sản phẩm |
| `/?q=nike` | Tìm kiếm sản phẩm |
| `/?new=1` | Hàng mới |
| `/?page=2` | Trang sản phẩm tiếp theo, tối đa 6 sản phẩm/trang |
| `/category/<slug>/` | Lọc theo danh mục |
| `/product/<slug>/` | Chi tiết sản phẩm |
| `/login/` | Đăng nhập |
| `/register/` | Đăng ký |
| `/admin/` | Trang quản trị Django |

Đăng nhập thành công sẽ chuyển về `/`.

## 5. Cách U01 hoạt động

- `Product/models.py`: `Category`, `Brand`, `Product`, `ProductImage`, `Banner`.
- `Product/views.py`: trang chủ, lọc danh mục, tìm kiếm, phân trang và chi tiết sản phẩm.
- `Product/context_processors.py`: tự động đưa danh mục đang hoạt động và số lượng giỏ hàng vào header.
- `Product/templates/Product/Home.html`: trang chủ, kế thừa `templates/base.html`.
- `Product/templates/Product/Detail.html`: chi tiết sản phẩm.
- Mỗi trang có CSS riêng trong `Product/static/Product/css/`.
- Header/footer dùng chung ở `templates/header.html` và `templates/footer.html`.

Danh mục mới có `is_active=True` sẽ tự xuất hiện trên menu, không phải sửa HTML. Sản phẩm hoặc thương hiệu tắt hoạt động sẽ không hiển thị ngoài website. Banner chỉ xuất hiện khi đang bật và thời gian hiện tại nằm trong khoảng `starts_at`–`ends_at`.

## 6. Quản trị dữ liệu

Tạo tài khoản admin:

```powershell
python manage.py createsuperuser
```

Vào `/admin/` để thêm/sửa danh mục, thương hiệu, sản phẩm, ảnh phụ và banner. Khi thêm sản phẩm mới, nên nhập tên tiếng Việt, chọn thương hiệu/danh mục, tải ảnh rõ nét và bật `is_active`.

## 7. Kiểm tra dự án

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Test U01 kiểm tra phân trang 6 sản phẩm, menu động, tìm kiếm tiếng Việt, lọc danh mục, ẩn sản phẩm, lịch banner, trạng thái rỗng và luồng trang chủ → chi tiết sản phẩm.

## 8. Lỗi thường gặp

- Không kết nối PostgreSQL: kiểm tra service PostgreSQL, database, mật khẩu và port `5432`.
- Báo thiếu `DB_PASSWORD`: khai báo các biến môi trường ở mục 2 trong đúng cửa sổ PowerShell đang chạy server.
- CSS chưa cập nhật: nhấn `Ctrl + F5` và kiểm tra đang sửa đúng CSS của trang.
- Ảnh không hiện: chạy lại `python manage.py seed_products --refresh-images`; giao diện có ảnh mặc định nếu file ảnh lỗi.

## 9. Quy ước phát triển tiếp

Mỗi nhóm chức năng lớn tạo một Django app riêng, ví dụ sản phẩm thuộc app `Product`, tài khoản thuộc app `Login`. Mỗi file HTML dùng một file CSS riêng và các trang con phải `{% extends 'base.html' %}`, chỉ thay nội dung trong `{% block content %}`.
