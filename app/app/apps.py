from django.contrib.admin.apps import AdminConfig


class JustInTimeAdminConfig(AdminConfig):
    default_site = 'app.admin.JustInTimeAdminSite'
