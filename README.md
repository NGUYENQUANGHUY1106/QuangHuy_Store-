# QuangHuy Store

Website bán giày và quần áo bóng đá bằng Django + PostgreSQL. U01 đã hoàn thành trang chủ và điều hướng sản phẩm. U02 đã hoàn thành trang danh mục, biến thể sản phẩm, bộ lọc nâng cao, sắp xếp và phân trang theo query string.

## 1. Cài đặt

Mở PowerShell tại thư mục có `manage.py` rồi chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 2. Cấu hình PostgreSQL

Tạo database `QuangHuy_Store`, sau đó tạo file `.env` cạnh file `manage.py`:

```text
DB_NAME=QuangHuy_Store
DB_USER=postgres
DB_PASSWORD=MAT_KHAU_POSTGRES_CUA_BAN
DB_HOST=localhost
DB_PORT=5432
```

Các biến mẫu nằm trong `.env.example`. File `.env` được đọc tự động và đã nằm trong `.gitignore`, vì vậy mật khẩu không được đẩy lên GitHub.

## 3. Tạo bảng và nạp dữ liệu U01 U02

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
- 200 biến thể gồm SKU, size, màu sắc, giá riêng, tồn kho và trạng thái hoạt động.
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
| `/category/<slug>/?brand=nike&size=42&color=Đen&in_stock=1` | Kết hợp bộ lọc U02 |
| `/category/<slug>/?sort=price_asc&page=2` | Sắp xếp và phân trang U02 |
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

## 6. Cách U02 hoạt động

- `Category.parent` hỗ trợ danh mục cha–con; trang danh mục cha tự lấy sản phẩm của các danh mục con.
- `ProductVariant` lưu SKU, size, màu sắc, giá, tồn kho và trạng thái hoạt động.
- `Product.gender` dùng để lọc Nam, Nữ hoặc Unisex; `Product.popularity` dùng để sắp xếp phổ biến.
- `Product/templates/Product/Category.html` là trang danh mục riêng, kế thừa `base.html`.
- `Product/static/Product/css/category.css` là CSS riêng của trang danh mục.
- Bộ lọc hỗ trợ thương hiệu, giới tính, size, màu, khoảng giá và chỉ sản phẩm còn hàng.
- Sắp xếp hỗ trợ mới nhất, giá tăng, giá giảm và phổ biến nhất.
- Mọi bộ lọc được giữ trên query string, vì vậy có thể sao chép URL hoặc chuyển trang mà không mất điều kiện.
- Giá chỉ được lọc từ biến thể đang hoạt động; sản phẩm, danh mục hoặc thương hiệu đã tắt không xuất hiện.
- Trên mobile, bộ lọc được thu gọn trong nút `BỘ LỌC SẢN PHẨM`.

## 7. Quản trị dữ liệu

Tạo tài khoản admin:

```powershell
python manage.py createsuperuser
```

Vào `/admin/` để thêm/sửa danh mục, thương hiệu, sản phẩm, biến thể, ảnh phụ và banner. Khi thêm sản phẩm mới, cần tạo ít nhất một biến thể đang hoạt động để sản phẩm xuất hiện trong trang danh mục U02.

## 8. Kiểm tra dự án

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

22 test hiện kiểm tra U01 và U02: phân trang 6 sản phẩm, giữ bộ lọc trên query string, menu động, tìm kiếm tiếng Việt, lọc kép, size/màu/giá/tồn kho, sắp xếp, danh mục cha–con, giá không hợp lệ, danh mục không tồn tại, trạng thái rỗng và luồng trang chủ → chi tiết sản phẩm.

## 9. Lỗi thường gặp

- Không kết nối PostgreSQL: kiểm tra service PostgreSQL, database, mật khẩu và port `5432`.
- Báo thiếu `DB_PASSWORD`: kiểm tra file `.env` có nằm cạnh `manage.py` và không có dấu `\` ở cuối dòng.
- CSS chưa cập nhật: nhấn `Ctrl + F5` và kiểm tra đang sửa đúng CSS của trang.
- Ảnh không hiện: chạy lại `python manage.py seed_products --refresh-images`; giao diện có ảnh mặc định nếu file ảnh lỗi.

## 10. Quy ước phát triển tiếp

Mỗi nhóm chức năng lớn tạo một Django app riêng, ví dụ sản phẩm thuộc app `Product`, tài khoản thuộc app `Login`. Mỗi file HTML dùng một file CSS riêng và các trang con phải `{% extends 'base.html' %}`, chỉ thay nội dung trong `{% block content %}`.
