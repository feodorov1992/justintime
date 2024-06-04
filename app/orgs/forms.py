from django.forms import ModelForm

from orgs.models import Organisation


class OrgForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Organisation
        exclude = 'is_client', 'is_expeditor'
