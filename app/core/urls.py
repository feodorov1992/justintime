from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='orders_list'), name='home'),
    path('favicon.ico', RedirectView.as_view(url=static('img/icons/favicon.ico')), name='favicon'),
    path('icon.svg', RedirectView.as_view(url=static('img/icons/icon.svg')), name='icon'),
    path('apple-touch-icon.png', RedirectView.as_view(url=static('img/icons/apple-touch-icon.png')),
         name='apple-touch-icon'),
    path('icon-192.png', RedirectView.as_view(url=static('img/icons/icon-192.png')), name='icon-192'),
    path('icon-512.png', RedirectView.as_view(url=static('img/icons/icon-512.png')), name='icon-512.png'),
    path('manifest.webmanifest', RedirectView.as_view(url=static('img/icons/manifest.webmanifest')), name='manifest'),
]
