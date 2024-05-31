from django.urls import path

from app_auth.views import LoginView

urlpatterns = [
    path('login', LoginView.as_view(), name='login')
]
