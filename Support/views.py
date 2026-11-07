import time
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404,redirect,render
from django.urls import reverse
from django.utils import timezone
from Login.models import User
from Product.models import Category,Product
from .models import BlogPost,FAQ,Notification,StaticPage,SupportMessage,SupportTicket

def user(request):
    uid=request.session.get('user_id');return User.objects.filter(id=uid,is_active=True).first() if uid else None
def valid_attachment(file):return not file or (file.size<=3*1024*1024 and getattr(file,'content_type','') in {'image/jpeg','image/png','application/pdf'})

def notification_list(request):
    current=user(request)
    if not current:return redirect('login')
    return render(request,'Support/Notifications.html',{'notifications':current.notifications.all()})
def notification_read(request,notification_id):
    current=user(request)
    if not current:return redirect('login')
    item=get_object_or_404(Notification,id=notification_id,user=current)
    if request.method=='POST':item.is_read=True;item.save(update_fields=['is_read'])
    return redirect(item.link or 'notification_list')

def ticket_list(request):
    current=user(request)
    if not current:return redirect('login')
    return render(request,'Support/Tickets.html',{'tickets':current.support_tickets.all()})
def ticket_create(request):
    current=user(request)
    if not current:return redirect('login')
    if request.method=='POST':
        now=int(time.time());recent=[x for x in request.session.get('ticket_times',[]) if now-x<3600]
        if len(recent)>=3:messages.error(request,'Bạn gửi yêu cầu quá nhanh. Vui lòng thử lại sau.');return redirect('ticket_create')
        category=request.POST.get('category','').strip();subject=request.POST.get('subject','').strip();text=request.POST.get('message','').strip();attachment=request.FILES.get('attachment')
        if not category or len(subject)<5 or len(text)<10 or not valid_attachment(attachment):messages.error(request,'Thông tin hoặc file đính kèm không hợp lệ.')
        else:
            ticket=SupportTicket.objects.create(user=current,category=category,subject=subject)
            SupportMessage.objects.create(ticket=ticket,sender=current,message=text,attachment=attachment or '')
            recent.append(now);request.session['ticket_times']=recent
            return redirect('ticket_detail',ticket_id=ticket.id)
    return render(request,'Support/TicketCreate.html')
def ticket_detail(request,ticket_id):
    current=user(request)
    if not current:return redirect('login')
    ticket=get_object_or_404(SupportTicket.objects.prefetch_related('messages'),id=ticket_id,user=current)
    if request.method=='POST' and ticket.status!='closed':
        text=request.POST.get('message','').strip();attachment=request.FILES.get('attachment')
        if len(text)>=2 and valid_attachment(attachment):SupportMessage.objects.create(ticket=ticket,sender=current,message=text,attachment=attachment or '')
        else:messages.error(request,'Tin nhắn hoặc file không hợp lệ.')
        return redirect('ticket_detail',ticket_id=ticket.id)
    return render(request,'Support/TicketDetail.html',{'ticket':ticket})
def faq_page(request):return render(request,'Support/FAQ.html',{'faqs':FAQ.objects.filter(is_active=True)})
def blog_list(request):
    posts=BlogPost.objects.filter(status='published',published_at__lte=timezone.now())
    return render(request,'Support/BlogList.html',{'posts':posts})
def blog_detail(request,slug):
    post=get_object_or_404(BlogPost,slug=slug,status='published',published_at__lte=timezone.now())
    return render(request,'Support/BlogDetail.html',{'post':post})

PAGE_DEFAULTS={
 'gioi-thieu':('Giới thiệu','QuangHuy Store cung cấp giày và trang phục bóng đá, hỗ trợ chọn đúng SKU, size và màu.'),
 'lien-he':('Liên hệ','Email support@quanghuystore.vn · Hotline 0900 000 000.'),
 'dieu-khoan':('Điều khoản mua hàng','Khách xác nhận sản phẩm, địa chỉ và thanh toán COD trước khi đặt đơn.'),
 'quyen-rieng-tu':('Quyền riêng tư','Thông tin tài khoản chỉ dùng để xử lý đơn, giao hàng và hỗ trợ khách hàng.'),
 'van-chuyen':('Chính sách vận chuyển','Phí và ETA là ước tính theo khu vực, phương thức và giá trị đơn tại checkout.'),
 'doi-tra-hoan-tien':('Đổi trả và hoàn tiền','Yêu cầu đổi/trả áp dụng cho đơn hoàn tất trong 7 ngày và do Admin xác nhận.'),
 'doi-size':('Chính sách đổi size','Khách gửi yêu cầu đổi size trong thời hạn và số lượng đã mua hợp lệ.'),
}
def static_page(request,slug):
    page=StaticPage.objects.filter(slug=slug,is_active=True).first()
    if not page:
        default=PAGE_DEFAULTS.get(slug)
        if not default:return error_404(request,None)
        page={'title':default[0],'content':default[1],'meta_description':default[1][:160],'slug':slug}
    return render(request,'Support/StaticPage.html',{'page':page})
def sitemap(request):
    urls=[request.build_absolute_uri(reverse('home'))]
    urls += [request.build_absolute_uri(reverse('product_by_category',args=[x.slug])) for x in Category.objects.filter(is_active=True)]
    urls += [request.build_absolute_uri(reverse('product_detail',args=[x.slug])) for x in Product.objects.filter(is_active=True)]
    urls += [request.build_absolute_uri(reverse('static_page',args=[slug])) for slug in PAGE_DEFAULTS]
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{url}</loc></url>' for url in urls)+'</urlset>'
    return HttpResponse(xml,content_type='application/xml')
def robots(request):return HttpResponse('User-agent: *\nAllow: /\nDisallow: /account/\nDisallow: /cart/\nDisallow: /checkout/\nDisallow: /admin/\nSitemap: '+request.build_absolute_uri('/sitemap.xml'),content_type='text/plain')
def error_404(request,exception):return render(request,'errors/404.html',status=404)
def error_500(request):return render(request,'errors/500.html',status=500)
