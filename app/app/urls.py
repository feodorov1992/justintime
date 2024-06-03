"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', include('logistics.urls')),
    path('auth/', include('app_auth.urls')),
    path('select2/', include("django_select2.urls")),
    path('admin/login/', RedirectView.as_view(pattern_name='login')),
    path('admin/logout/', RedirectView.as_view(pattern_name='logout')),
    path('admin/', admin.site.urls),
]
