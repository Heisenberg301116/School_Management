from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect(reverse_lazy('dashboard'), permanent=True)),
    path('admin/', admin.site.urls),
    path('inquiries/', include('inquiries.urls')),
]
