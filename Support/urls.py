from django.urls import path
from . import views
urlpatterns=[path('account/notifications/',views.notification_list,name='notification_list'),path('account/notifications/<int:notification_id>/read/',views.notification_read,name='notification_read'),path('support/tickets/',views.ticket_list,name='ticket_list'),path('support/tickets/create/',views.ticket_create,name='ticket_create'),path('support/tickets/<int:ticket_id>/',views.ticket_detail,name='ticket_detail'),path('faqs/',views.faq_page,name='faq')]
