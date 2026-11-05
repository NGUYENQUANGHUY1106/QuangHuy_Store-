import time
from django.contrib import messages
from django.shortcuts import get_object_or_404,redirect,render
from Login.models import User
from .models import FAQ,Notification,SupportMessage,SupportTicket

def user(request):
    uid=request.session.get('user_id');return User.objects.filter(id=uid).first() if uid else None
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
