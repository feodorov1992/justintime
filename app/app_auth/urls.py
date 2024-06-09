from django.urls import path

from app_auth.views import LoginView, LogoutView, UserEditView, UserAddView, OrgEditView, PasswordChangeView, \
    PasswordResetConfirmView, send_confirmation_email, PasswordResetView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserEditView.as_view(), name='user_edit'),
    path('org/', OrgEditView.as_view(), name='org_edit'),
    path('user_add/', UserAddView.as_view(), name='user_add'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('reset_password/', PasswordResetView.as_view(), name='reset_password'),
    path('send_confirmation_email/<uuid:pk>/', send_confirmation_email, name='send_confirmation_email'),
    path('registration_confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(),
         name='registration_confirm'),
]
