from django.urls import path
from . import views
urlpatterns=[path('account/notifications/',views.notification_list,name='notification_list'),path('account/notifications/<int:notification_id>/read/',views.notification_read,name='notification_read'),path('support/tickets/',views.ticket_list,name='ticket_list'),path('support/tickets/create/',views.ticket_create,name='ticket_create'),path('support/tickets/<int:ticket_id>/',views.ticket_detail,name='ticket_detail'),path('faqs/',views.faq_page,name='faq')]
urlpatterns += [path('pages/<slug:slug>/',views.static_page,name='static_page'),path('sitemap.xml',views.sitemap,name='sitemap'),path('robots.txt',views.robots,name='robots')]
urlpatterns += [path('blogs/',views.blog_list,name='blog_list'),path('blogs/<slug:slug>/',views.blog_detail,name='blog_detail')]
