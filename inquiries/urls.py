from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('list/', views.inquiry_list, name='inquiry_list'),
    path('add_inquiry/', views.add_inquiry, name='add_inquiry'),
    path('agents_performance/', views.agent_performance, name='agent_performance'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/', views.export_inquiries_excel,name='export_inquiries_csv'),
    path('remove_lead/', views.remove_agent_view, name='remove_lead'),
    path('reassign_lead/', views.assign_lead, name='assign_lead'),        
    path('update_status/<int:inquiry_id>/', views.manage_lead_status, name='update_status'),
    path('delete_inquiry/<int:id>/', views.delete_inquiry, name='delete_inquiry'),
    
    path('agents/', views.agent_list, name='agent_list'),
    path('agents/add/', views.add_agent, name='add_agent'),
    
    path('login/', views.agent_login, name='login'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]