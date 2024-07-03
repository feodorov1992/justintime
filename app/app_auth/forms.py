from django import forms

from app_auth.models import User
from logistics.filtersets import ManagerWidget
from orgs.models import Organisation


class UserForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = User
        fields = 'username', 'last_name', 'first_name', 'second_name', 'main_manager'
        widgets = {
            'main_manager': ManagerWidget
        }


class OrgForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Organisation
        fields = 'inn', 'kpp', 'ogrn', 'legal_name', 'legal_address', 'fact_address', 'email'
