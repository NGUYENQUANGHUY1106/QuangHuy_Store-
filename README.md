# QuangHuy Store

Website bán giày và quần áo bóng đá bằng Django + PostgreSQL. Toàn bộ phần User U01–U17 đã hoàn thành; thanh toán hiện chỉ dùng COD theo yêu cầu.

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
| `/products/?q=nike` | Trang kết quả tìm kiếm U03 |
| `/products/suggest/?q=nike` | API gợi ý tối đa 8 sản phẩm |
| `/?new=1` | Hàng mới |
| `/?page=2` | Trang sản phẩm tiếp theo, tối đa 6 sản phẩm/trang |
| `/category/<slug>/` | Lọc theo danh mục |
| `/category/<slug>/?brand=nike&size=42&color=Đen&in_stock=1` | Kết hợp bộ lọc U02 |
| `/category/<slug>/?sort=price_asc&page=2` | Sắp xếp và phân trang U02 |
| `/product/<slug>/` | Chi tiết sản phẩm |
| `/product/<slug>/variants/` | API size, màu, SKU, giá và tồn kho U04 |
| `/product/<slug>/add-to-cart/` | POST biến thể và số lượng đã được kiểm tra |
| `/cart/` | Trang giỏ hàng của khách hoặc người đã đăng nhập |
| `/cart/items/add/` | POST thêm đúng biến thể vào giỏ |
| `/cart/items/<id>/update/` | POST cập nhật số lượng |
| `/cart/items/<id>/select/` | POST chọn sản phẩm để thanh toán |
| `/cart/items/<id>/delete/` | POST xóa một sản phẩm khỏi giỏ |
| `/cart/clear/` | POST xóa toàn bộ giỏ |
| `/checkout/` | Chọn địa chỉ, vận chuyển, thanh toán và đặt đơn |
| `/checkout/success/<order_code>/` | Trang xác nhận đơn của đúng khách hàng |
| `/payments/<order_code>/status/` | API trạng thái thanh toán COD của chủ đơn |
| `/account/orders/` | Danh sách đơn của khách, lọc trạng thái và phân trang |
| `/account/orders/<order_code>/` | Chi tiết snapshot, thanh toán và timeline đơn |
| `/account/orders/<order_code>/cancel/` | POST hủy đơn khi còn được phép |
| `/account/orders/<order_code>/reorder/` | POST mua lại các SKU còn bán/còn hàng |
| `/account/wishlist/` | Danh sách sản phẩm yêu thích của khách |
| `/account/wishlist/toggle/<product_id>/` | POST thêm/xóa yêu thích không tải lại trang |
| `/products/compare/?ids=1&ids=2` | So sánh 2–4 sản phẩm cùng danh mục |
| `/reviews/product/<product_id>/create/` | POST đánh giá sản phẩm đã mua và hoàn tất |
| `/reviews/<review_id>/edit/` | POST sửa đánh giá của chính mình |
| `/reviews/<review_id>/delete/` | POST xóa đánh giá của chính mình |
| `/reviews/<review_id>/report/` | POST báo cáo đánh giá vi phạm |
| `/questions/product/<product_id>/create/` | POST gửi câu hỏi sản phẩm |
| `/checkout/apply-coupon/` | POST xem trước số tiền giảm phía server |
| `/promotions/active/` | API chương trình khuyến mãi đang hiệu lực |
| `/shipping/options/?address_id=<id>` | Phí ship và ETA theo địa chỉ/giỏ |
| `/account/orders/<code>/shipment/` | Tracking vận đơn của đúng chủ đơn |
| `/account/returns/` | Lịch sử yêu cầu đổi/trả của khách |
| `/account/orders/<code>/return/` | Tạo yêu cầu đổi/trả cho đơn đủ điều kiện |
| `/account/returns/<id>/` | Chi tiết yêu cầu của đúng chủ sở hữu |
| `/account/notifications/` | Thông báo cá nhân và đánh dấu đã đọc |
| `/support/tickets/` | Danh sách hội thoại hỗ trợ của khách |
| `/support/tickets/create/` | Tạo ticket có giới hạn tần suất/file an toàn |
| `/faqs/` | Câu hỏi thường gặp công khai |
| `/pages/<slug>/` | Giới thiệu, liên hệ và các chính sách công khai |
| `/sitemap.xml` | Sitemap sản phẩm, danh mục và trang thông tin |
| `/robots.txt` | Quy tắc index và chặn trang riêng tư |
| `/login/` | Đăng nhập |
| `/register/` | Đăng ký |
| `/logout/` | POST đăng xuất, vẫn giữ giỏ hàng trong session |
| `/account/` | Trang tài khoản, yêu cầu đăng nhập |
| `/account/change-password/` | POST đổi mật khẩu sau khi xác thực mật khẩu hiện tại |
| `/account/addresses/add/` | POST thêm địa chỉ giao hàng |
| `/account/addresses/<id>/edit/` | POST sửa đúng địa chỉ của người đang đăng nhập |
| `/account/addresses/<id>/default/` | POST chọn một địa chỉ mặc định |
| `/account/addresses/<id>/delete/` | POST xóa địa chỉ chưa dùng trong đơn |
| `/forgot-password/` | Yêu cầu liên kết đặt lại mật khẩu |
| `/reset-password/<token>/` | Đặt mật khẩu mới bằng token dùng một lần |
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

## 7. Cách U03 hoạt động

- Header gửi từ khóa tới `/products/` và hiển thị dropdown gợi ý khi nhập từ 2 ký tự.
- JavaScript chờ 300ms sau lần gõ cuối rồi mới gọi API, tránh gửi quá nhiều request.
- API `/products/suggest/` trả tối đa 8 sản phẩm gồm tên, thương hiệu, ảnh, giá và URL chi tiết.
- Có thể tìm theo tên sản phẩm, thương hiệu, danh mục hoặc SKU của biến thể.
- Trang kết quả sử dụng lại bộ lọc và sắp xếp của U02; query string được giữ khi phân trang.
- Từ khóa dài tối đa 80 ký tự; API gợi ý giới hạn 30 request/phút cho mỗi session.
- Nội dung gợi ý được tạo bằng `textContent`, còn Django template tự escape từ khóa để tránh chèn HTML.
- Lịch sử 5 từ khóa gần nhất được lưu phía trình duyệt bằng `localStorage`.

## 8. Cách U04 hoạt động

- Trang chi tiết có ảnh lớn, thumbnail, hiệu ứng zoom, mô tả, giá và sản phẩm liên quan.
- API biến thể trả ID, SKU, size, màu, giá gốc, giá khuyến mãi, tồn kho và ảnh.
- Khi đổi size/màu, JavaScript cập nhật đúng SKU, giá, ảnh, tồn kho và giới hạn số lượng.
- Biến thể hết hàng tự vô hiệu hóa nút thêm giỏ và mua ngay.
- Server luôn đọc giá và tồn kho từ PostgreSQL; không nhận giá do client gửi lên.
- Size/màu là bắt buộc; số lượng phải từ 1 đến tồn kho còn lại.
- CTA thêm giỏ lưu biến thể và số lượng vào session, đồng thời cập nhật badge header. U07 sẽ mở rộng phần này thành trang giỏ hàng hoàn chỉnh.
- CTA mua ngay lưu biến thể đã kiểm tra để U08 sử dụng khi xây checkout.
- Có bảng quy đổi size giày EU/US/UK và link chính sách đổi size.

## 9. Cách U05 hoạt động

- Đăng ký kiểm tra đủ dữ liệu, email hợp lệ, số điện thoại 10 số, avatar là ảnh và mật khẩu có ít nhất 8 ký tự gồm chữ và số.
- Email và tên tài khoản không được trùng; mật khẩu luôn được băm bằng bộ mã hóa của Django trước khi lưu.
- Đăng nhập tạo session mới để tránh session fixation, hỗ trợ “ghi nhớ đăng nhập” và chỉ chuyển tới tham số `next` nằm trong chính website.
- Sau 10 lần đăng nhập sai trong 5 phút, session bị giới hạn tạm thời để giảm thử mật khẩu tự động.
- `/account/` là trang được bảo vệ. Đăng xuất chỉ nhận POST có CSRF và vẫn giữ giỏ hàng khách trong session.
- Quên mật khẩu luôn trả cùng một thông báo dù email có tồn tại hay không, tránh làm lộ danh sách tài khoản.
- Token đặt lại mật khẩu chỉ lưu bản băm trong database, hết hạn sau 30 phút và chỉ dùng được một lần.
- Email phát triển được in ra terminal bằng `console.EmailBackend`. Có thể đổi `EMAIL_BACKEND` bằng biến môi trường khi cấu hình dịch vụ gửi thư thật.

## 10. Cách U06 hoạt động

- Trang `/account/` cho phép khách tự sửa họ tên, email, điện thoại và avatar tùy chọn; email/tên tài khoản vẫn phải duy nhất.
- Đổi mật khẩu chỉ thành công khi mật khẩu hiện tại đúng; mật khẩu mới tiếp tục được băm bằng bộ mã hóa của Django.
- Mỗi tài khoản có nhiều `Address`, gồm người nhận, điện thoại, tỉnh/thành, phường/xã và địa chỉ chi tiết.
- Địa chỉ đầu tiên tự trở thành mặc định. Khi chọn địa chỉ mặc định khác, transaction tắt cờ mặc định ở các địa chỉ còn lại.
- Mọi thao tác sửa, xóa và chọn mặc định đều lọc đồng thời theo `address_id` và người đang đăng nhập, ngăn người A truy cập địa chỉ người B.
- Địa chỉ đã đánh dấu dùng trong đơn không thể bị xóa. U08 sẽ đánh dấu trường này khi tạo đơn hàng.
- Tab lịch sử đơn hàng và yêu thích đã có trên giao diện; dữ liệu đơn sẽ được nối ở U08.

## 11. Cách U07 hoạt động

- App `Cart` tách riêng, gồm `Cart` cho tài khoản hoặc guest session và `CartItem` tham chiếu đúng `ProductVariant` (SKU/size/màu).
- Thêm cùng SKU sẽ cộng số lượng; hai size khác nhau là hai dòng. Constraint ngăn một SKU bị lặp trong cùng giỏ.
- Server tự đọc giá và tồn kho từ database, không nhận giá do trình duyệt gửi. Số lượng luôn phải từ 1 đến tồn kho.
- Trang `/cart/` hiển thị ảnh, tên, SKU, size/màu, đơn giá hiện tại, số lượng, thành tiền và tổng tiền của các dòng đã chọn.
- Có cập nhật số lượng, chọn item thanh toán, xóa một dòng, xóa tất cả, trạng thái giỏ trống và cảnh báo đổi giá/hết hàng.
- Header có mini-cart và badge lấy trực tiếp từ database. JavaScript khóa nút sau khi submit để tránh bấm hai lần.
- Khi guest đăng nhập, giỏ guest được merge theo SKU vào giỏ tài khoản và giới hạn theo tồn kho.
- Mọi thao tác sửa/xóa đều lọc theo giỏ hiện tại nên không thể sửa `CartItem` của người khác.

## 12. Cách U08 hoạt động

- App `Checkout` tách riêng, gồm `Order`, `OrderItem`, `OrderAddress`, `Coupon` và `CouponUsage`.
- Checkout chỉ lấy các `CartItem` đã chọn và luôn đọc lại giá, trạng thái SKU và tồn kho ở server.
- Khách chọn địa chỉ trong sổ địa chỉ; đơn lưu một bản snapshot nên việc sửa địa chỉ sau này không làm đổi đơn cũ.
- Vận chuyển tiêu chuẩn 30.000₫, miễn phí từ 999.000₫; hỏa tốc 60.000₫. Tất cả phép tính dùng `Decimal`.
- Voucher được kiểm tra trạng thái, thời gian, giá trị đơn tối thiểu và giới hạn một lần cho mỗi khách.
- Khi đặt đơn, server khóa các biến thể bằng transaction, kiểm tra tồn, tạo đơn và item, trừ tồn rồi chỉ xóa các dòng giỏ đã mua.
- `idempotency_key` ngăn bấm/gửi lại request tạo hai đơn giống nhau.
- COD tạo đơn chờ xử lý; online tạo đơn chờ để U09 nối cổng thanh toán.

## 13. Cách U09 hoạt động (chỉ COD)

- Theo yêu cầu hiện tại, website chỉ hiển thị thanh toán khi nhận hàng; lựa chọn online đã được bỏ khỏi checkout.
- Mỗi đơn tạo một `Payment` riêng với phương thức `cod`, số tiền bằng tổng đơn và trạng thái ban đầu `pending` (chờ thu tiền).
- Trạng thái thanh toán độc lập với trạng thái đơn hàng; Admin sẽ xác nhận `paid` khi giao hàng và thu tiền thành công.
- API trạng thái chỉ cho đúng chủ đơn truy cập, người khác nhận 404.
- Không có secret, callback hay webhook online trong source code. Phần online được tạm bỏ qua theo yêu cầu.

## 14. Cách U10 hoạt động

- “Đơn hàng của tôi” chỉ truy vấn đơn thuộc tài khoản hiện tại, hỗ trợ lọc trạng thái và tối đa 10 đơn mỗi trang.
- Chi tiết đơn hiển thị snapshot tên/SKU/size/màu/giá, địa chỉ giao hàng, COD và timeline trạng thái.
- `OrderStatusHistory` lưu từng mốc trạng thái để không phụ thuộc riêng trạng thái hiện tại.
- Khách chỉ được hủy đơn `pending` hoặc `confirmed`. Transaction khóa đơn/SKU, hoàn tồn đúng một lần và chuyển COD sang thất bại.
- Đơn đang giao, hoàn tất hoặc đã hủy không thể hủy lần nữa.
- Mua lại dùng SKU hiện tại: SKU còn bán/còn tồn được thêm vào giỏ; SKU không khả dụng được bỏ qua và thông báo rõ.
- URL danh sách, chi tiết, hủy và mua lại đều kiểm tra ownership để ngăn xem/sửa đơn của người khác.

## 15. Cách U11 hoạt động

- App `Engagement` lưu `WishlistItem` và `RecentlyViewed` theo tài khoản; constraint ngăn cùng sản phẩm bị lưu trùng.
- Nút trái tim có trên product-card và trang chi tiết, dùng `fetch` POST có CSRF để thêm/xóa không tải lại trang.
- Wishlist chỉ hiển thị dữ liệu của người đang đăng nhập; sản phẩm ngừng bán vẫn được giữ để khách nhận biết.
- Trang so sánh nhận tối đa 4 sản phẩm và chỉ chấp nhận sản phẩm cùng danh mục; hiển thị giá, loại, thương hiệu, chất liệu và size.
- Sản phẩm đã xem được lưu trong database khi đăng nhập, hoặc tối đa 10 ID trong session đối với guest.
- Trang chi tiết hiển thị hàng sản phẩm đã xem gần đây, không lặp sản phẩm hiện tại.

## 16. Cách U12 hoạt động

- App `Reviews` gồm `Review`, `ReviewImage`, `ReviewReport` và `ProductQuestion`.
- Chỉ khách có `OrderItem` thuộc đơn `completed` của đúng sản phẩm mới được đánh giá và có nhãn “Đã mua hàng”.
- Mỗi khách chỉ có một review cho một sản phẩm; rating bắt buộc 1–5 và bình luận tối thiểu 5 ký tự.
- Mỗi review nhận tối đa 3 ảnh, mỗi ảnh tối đa 2 MB và MIME phải là ảnh.
- Trang chi tiết hiển thị trung bình sao, lọc theo số sao và phân trang 5 review; Django tự escape nội dung chống chèn HTML/XSS.
- Khách chỉ sửa/xóa review của mình. Khách đăng nhập có thể báo cáo review vi phạm và đặt câu hỏi sản phẩm.
- Review bị báo cáo chuyển sang trạng thái chờ Admin kiểm tra và không còn xuất hiện công khai.

## 17. Cách U13 hoạt động

- Voucher kiểm tra thời gian, giá trị đơn tối thiểu, quota tổng và một lượt cho mỗi khách.
- API preview tính giảm giá từ giỏ đã chọn; không nhận số tiền giảm từ client.
- Khi tạo đơn, transaction khóa coupon, tăng `used_count` và lưu `OrderDiscount` snapshot.
- Tổng giảm không vượt tiền hàng. Hủy đơn hợp lệ xóa lượt dùng và hoàn quota coupon.
- `Promotion` cung cấp danh sách chương trình công khai đang còn hiệu lực.

## 18. Cách U14 hoạt động

- `ShippingMethod` và `ShippingZone` cấu hình phí cơ bản, phụ phí tỉnh, ngưỡng miễn ship và ETA.
- Nếu chưa cấu hình, hệ thống dùng tiêu chuẩn 30.000₫/miễn từ 999.000₫ và hỏa tốc 60.000₫.
- Checkout tính lại lựa chọn giao hàng theo địa chỉ; địa chỉ ngoài vùng bị từ chối.
- `Shipment` và `ShipmentEvent` lưu hãng, tracking, ETA và timeline; `event_id` duy nhất chống sự kiện trùng.
- API tracking và chi tiết đơn chỉ hiển thị vận đơn cho đúng chủ đơn, không lộ địa chỉ qua API.

## 19. Cách U15 hoạt động

- Chỉ đơn `completed` trong 7 ngày mới tạo được yêu cầu đổi/trả.
- Khách chọn item, số lượng không vượt phần đã mua chưa yêu cầu, loại yêu cầu và lý do.
- Tối đa 3 ảnh minh chứng, mỗi ảnh không quá 2 MB và phải có MIME ảnh.
- Chống nộp lặp vượt số lượng; khách chỉ xem yêu cầu của mình.
- Trạng thái gồm pending/reviewing/approved/rejected/received/refunded/replaced; User không tự hoàn tiền.

## 20. Cách U16 hoạt động

- Tạo thông báo khi đặt đơn và gửi yêu cầu đổi/trả; khách đánh dấu đã đọc và mở đúng liên kết liên quan.
- Ticket có danh mục, tiêu đề, hội thoại, trạng thái và file JPG/PNG/PDF tối đa 3 MB.
- Chỉ chủ ticket được xem/gửi phản hồi; ticket đóng không nhận tin mới.
- Mỗi session chỉ tạo tối đa 3 ticket/giờ để hạn chế spam.
- FAQ là trang công khai; email/số điện thoại khách không xuất hiện trong danh sách công khai.

## 21. Cách U17 hoạt động

- Có trang giới thiệu, liên hệ, điều khoản, quyền riêng tư, vận chuyển, đổi trả/hoàn tiền và đổi size; Admin có thể quản lý bằng `StaticPage`.
- Product/Category có `seo_title` và `meta_description`; mọi trang có canonical và robots meta.
- Sitemap chỉ liệt kê trang công khai. Robots/noindex chặn account, cart, checkout, support và admin.
- 404/500 có thông báo hữu ích; ảnh co giãn, layout có breakpoint mobile và trang có skip-link.
- Tất cả link/nút/form chính có text hoặc aria-label; focus bàn phím được hiển thị rõ.

## 22. Checkpoint phần User

- Visitor có thể tìm, lọc, chọn đúng biến thể, thêm giỏ và checkout COD.
- Customer có thể đăng ký, đăng nhập, lưu địa chỉ, đặt/hủy/mua lại đơn và nhận thông báo.
- Giá, voucher, phí ship, tồn kho và tổng tiền đều do server tính; đơn lưu snapshot và chống submit trùng.
- Có wishlist, so sánh, review đã mua, tracking, đổi trả, ticket hỗ trợ và chính sách công khai.
- Các trường hợp hết tồn, sai giá, voucher hết hạn/quota, IDOR và file giả đều có test.

## 23. Quản trị dữ liệu

Tạo tài khoản admin:

```powershell
python manage.py createsuperuser
```

Vào `/admin/` để thêm/sửa danh mục, thương hiệu, sản phẩm, biến thể, ảnh phụ và banner. Khi thêm sản phẩm mới, cần tạo ít nhất một biến thể đang hoạt động để sản phẩm xuất hiện trong trang danh mục U02.

## 24. Kiểm tra dự án

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Toàn bộ test hiện kiểm tra U01–U08, gồm giỏ hàng, checkout item đã chọn, snapshot địa chỉ, voucher/phí ship, tồn kho, rollback, IDOR và chống tạo đơn trùng.

## 25. Lỗi thường gặp

- Không kết nối PostgreSQL: kiểm tra service PostgreSQL, database, mật khẩu và port `5432`.
- Báo thiếu `DB_PASSWORD`: kiểm tra file `.env` có nằm cạnh `manage.py` và không có dấu `\` ở cuối dòng.
- CSS chưa cập nhật: nhấn `Ctrl + F5` và kiểm tra đang sửa đúng CSS của trang.
- Ảnh không hiện: chạy lại `python manage.py seed_products --refresh-images`; giao diện có ảnh mặc định nếu file ảnh lỗi.

## 26. Quy ước phát triển tiếp

Mỗi nhóm chức năng lớn tạo một Django app riêng, ví dụ sản phẩm thuộc app `Product`, tài khoản thuộc app `Login`. Mỗi file HTML dùng một file CSS riêng và các trang con phải `{% extends 'base.html' %}`, chỉ thay nội dung trong `{% block content %}`.

## 27. A01 - Đăng nhập Admin, vai trò và phân quyền

Phần quản trị custom nằm trong app riêng `AdminPanel` và dùng đường dẫn `/management/`. Đường dẫn `/admin/` vẫn là Django admin kỹ thuật để seed hoặc sửa dữ liệu khi phát triển.

Chạy migration mới:

```powershell
python manage.py migrate
```

Tạo tài khoản quản trị toàn quyền:

```powershell
python manage.py createsuperuser
```

Tạo tài khoản nhân viên theo vai trò; lệnh sẽ hỏi mật khẩu hai lần và không ghi mật khẩu vào source code hoặc command history:

```powershell
python manage.py create_admin_staff --username product_staff --email product@example.com --role PRODUCT
```

Các vai trò hỗ trợ: `PRODUCT`, `WAREHOUSE`, `ORDER`, `SUPPORT`, `MARKETING`, `FINANCE`.

Sau khi tạo tài khoản, mở `http://127.0.0.1:8000/management/login/`. Mỗi nhân viên chỉ thấy menu và gọi được endpoint thuộc vai trò của mình; superuser có toàn quyền. Tài khoản `is_staff=True` nhưng chưa có `StaffProfile` sẽ bị từ chối theo nguyên tắc mặc định không cấp quyền.

A01 hiện có:

- Trang đăng nhập Admin riêng, đăng xuất bằng POST, session tối đa 8 giờ và giới hạn 10 lần đăng nhập sai trong 5 phút.
- Vai trò nghiệp vụ và permission matrix kiểm tra ở backend, không chỉ ẩn menu giao diện.
- Trang tổng quan khung, trang 403, API `/management/me/` và form đổi mật khẩu giữ nguyên phiên đăng nhập.
- `AuditLog` ghi đăng nhập, đăng xuất, đổi mật khẩu và lần đăng nhập thất bại; không ghi mật khẩu.
- Giao diện dùng `AdminPanel/templates/AdminPanel/base_admin.html` và static riêng, không trộn với giao diện khách hàng.

Kiểm tra riêng A01:

```powershell
python manage.py test AdminPanel
```

## 28. A02 - Dashboard vận hành

Mở `http://127.0.0.1:8000/management/` sau khi đăng nhập Admin. Dashboard dùng dữ liệu thật trong database và có bộ lọc `from/to` theo ngày, tối đa 366 ngày mỗi lần. Mốc đầu ngày/cuối ngày được tính theo múi giờ `Asia/Ho_Chi_Minh`.

Quy ước số liệu:

- Đơn trong kỳ được lọc theo `Order.created_at`; thẻ riêng hiển thị số đơn chờ, hoàn tất và đã hủy.
- Doanh thu đã thu là tổng `Payment.amount` có trạng thái `paid`, có `paid_at` trong kỳ và đơn không ở trạng thái `cancelled`.
- Chỉ superuser hoặc vai trò `FINANCE` thấy doanh thu; vai trò khác không nhận số liệu tài chính trong HTML.
- Danh sách đơn gần đây chỉ hiện cho người có quyền đơn hàng.
- Cảnh báo tồn thấp lấy SKU đang hoạt động, sản phẩm đang bán và `stock <= 5`; chỉ vai trò sản phẩm/kho hoặc superuser thấy.
- Dashboard còn có biểu đồ số đơn theo ngày, tổng tài khoản khách hàng và menu phân hệ theo vai trò.

Các câu lệnh kiểm tra A01–A02:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test AdminPanel
python manage.py test
```

## 29. A03 - Danh mục, thương hiệu và môn thể thao

Vai trò `PRODUCT` và superuser quản lý catalog tại:

- `/management/catalog/categories/`
- `/management/catalog/brands/`
- `/management/catalog/sports/`

Các trang hỗ trợ tìm kiếm, thêm, sửa và ẩn/hiện. Danh mục không bị xóa cứng khi đã có sản phẩm; form chặn slug/tên trùng và chặn cây danh mục vòng lặp. Mỗi thay đổi đều ghi `AuditLog`.

```powershell
python manage.py migrate
python manage.py test AdminPanel
```

## 30. A04 - Quản lý sản phẩm và hình ảnh

Vai trò `PRODUCT` quản lý tại `/management/products/`. Sản phẩm mới luôn ở trạng thái nháp; chỉ được công bố khi có ít nhất một SKU hoạt động. Trang hỗ trợ tìm kiếm theo tên/SKU, lọc trạng thái, sửa thông tin/SEO/hướng dẫn size, công bố, ẩn, ẩn hàng loạt, ảnh phụ tối đa 5 MB và xuất CSV. Sản phẩm được ẩn mềm để giữ lịch sử đơn hàng.

```powershell
python manage.py migrate
python manage.py test AdminPanel
```

## 31. A05 - Quản lý SKU size và màu

Từ trang sửa sản phẩm, chọn **Quản lý SKU** để thêm/sửa biến thể. Mỗi SKU có barcode, size, màu, giá, giá và lịch khuyến mãi, ảnh, tồn hiện tại và trạng thái bán. Hệ thống chặn SKU/barcode trùng, giá âm, giá sale cao hơn giá bán và khoảng thời gian sale sai; SKU đã có trong đơn hàng không được đổi mã.

```powershell
python manage.py migrate
python manage.py test AdminPanel
```

## 32. A06 - Kho hàng, điều chỉnh và kiểm kê

App riêng `Inventory` quản lý nhiều kho và tồn theo từng SKU tại `/management/inventory/`. `available = on_hand - reserved`; database chặn reserved vượt tồn. Điều chỉnh và hoàn tất kiểm kê dùng transaction/row lock, tạo `StockMovement`, đồng thời cập nhật tổng tồn online về `ProductVariant.stock`.

```powershell
python manage.py migrate
python manage.py test Inventory AdminPanel
```

## 33. A07 - Nhà cung cấp và nhập kho

Trang `/management/inventory/procurement/` quản lý nhà cung cấp, phiếu mua và nhận từng SKU. Phiếu đi từ draft → approved → partially_received → received. Mỗi mã phiếu nhận chỉ xử lý một lần; nhận hàng tăng tồn, cập nhật số đã nhận và ghi `StockMovement` trong transaction.

```powershell
python manage.py migrate
python manage.py test Inventory
```
