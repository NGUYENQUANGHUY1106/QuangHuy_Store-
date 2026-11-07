from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from Checkout.models import OrderItem
from Login.models import User
from Product.models import Product

from .models import ProductQuestion, Review, ReviewImage, ReviewReport


def current_user(request):
    user_id = request.session.get('user_id')
    return User.objects.filter(id=user_id, is_active=True).first() if user_id else None


def review_order_item(user, product):
    return OrderItem.objects.filter(
        order__user=user, order__status='completed', variant__product=product,
    ).order_by('-order__created_at').first()


def valid_review_images(files):
    if len(files) > 3:
        return 'Chỉ được tải tối đa 3 ảnh.'
    for image in files:
        if not getattr(image, 'content_type', '').startswith('image/'):
            return 'Tệp đánh giá phải là hình ảnh.'
        if image.size > 2 * 1024 * 1024:
            return 'Mỗi ảnh đánh giá không được vượt quá 2 MB.'
    return ''


@require_POST
def review_create(request, product_id):
    user = current_user(request)
    if not user:
        return redirect('/login/')
    product = get_object_or_404(Product, id=product_id)
    order_item = review_order_item(user, product)
    if not order_item:
        messages.error(request, 'Bạn chỉ có thể đánh giá sản phẩm đã mua và hoàn tất giao hàng.')
        return redirect('product_detail', product_slug=product.slug)
    if Review.objects.filter(user=user, product=product).exists():
        messages.error(request, 'Bạn đã đánh giá sản phẩm này.')
        return redirect('product_detail', product_slug=product.slug)
    try:
        rating = int(request.POST.get('rating', ''))
    except ValueError:
        rating = 0
    comment = request.POST.get('comment', '').strip()
    images = request.FILES.getlist('images')
    image_error = valid_review_images(images)
    if rating not in range(1, 6) or len(comment) < 5 or image_error:
        messages.error(request, image_error or 'Số sao phải từ 1–5 và bình luận có ít nhất 5 ký tự.')
        return redirect('product_detail', product_slug=product.slug)
    review = Review.objects.create(
        user=user, product=product, order_item=order_item, rating=rating, comment=comment,
    )
    for image in images:
        ReviewImage.objects.create(review=review, image=image)
    messages.success(request, 'Cảm ơn bạn đã đánh giá sản phẩm.')
    return redirect('product_detail', product_slug=product.slug)


@require_POST
def review_edit(request, review_id):
    user = current_user(request)
    if not user:
        return redirect('login')
    review = get_object_or_404(Review, id=review_id, user=user)
    try:
        rating = int(request.POST.get('rating', ''))
    except ValueError:
        rating = 0
    comment = request.POST.get('comment', '').strip()
    if rating not in range(1, 6) or len(comment) < 5:
        messages.error(request, 'Nội dung chỉnh sửa không hợp lệ.')
    else:
        review.rating = rating
        review.comment = comment
        review.save(update_fields=['rating', 'comment', 'updated_at'])
        messages.success(request, 'Đã cập nhật đánh giá.')
    return redirect('product_detail', product_slug=review.product.slug)


@require_POST
def review_delete(request, review_id):
    user = current_user(request)
    if not user:
        return redirect('login')
    review = get_object_or_404(Review, id=review_id, user=user)
    product_slug = review.product.slug
    review.delete()
    messages.success(request, 'Đã xóa đánh giá.')
    return redirect('product_detail', product_slug=product_slug)


@require_POST
def review_report(request, review_id):
    user = current_user(request)
    if not user:
        return redirect('login')
    review = get_object_or_404(Review, id=review_id)
    ReviewReport.objects.get_or_create(
        review=review, user=user, defaults={'reason': request.POST.get('reason', '').strip()[:255]},
    )
    review.status = 'reported'
    review.save(update_fields=['status'])
    messages.success(request, 'Đã gửi báo cáo đánh giá.')
    return redirect('product_detail', product_slug=review.product.slug)


@require_POST
def question_create(request, product_id):
    user = current_user(request)
    if not user:
        return redirect('login')
    product = get_object_or_404(Product, id=product_id)
    question = request.POST.get('question', '').strip()
    if len(question) < 5:
        messages.error(request, 'Câu hỏi phải có ít nhất 5 ký tự.')
    else:
        ProductQuestion.objects.create(user=user, product=product, question=question[:500])
        messages.success(request, 'Đã gửi câu hỏi về sản phẩm.')
    return redirect('product_detail', product_slug=product.slug)
