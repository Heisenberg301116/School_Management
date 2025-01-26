from django.urls import path
from . import views

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
]