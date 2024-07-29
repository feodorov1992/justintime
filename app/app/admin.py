from django.contrib import admin


class JustInTimeAdminSite(admin.AdminSite):
    site_header = 'Управление Just In Time'
    site_title = 'Just In Time'
