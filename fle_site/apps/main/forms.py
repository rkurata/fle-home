from django import forms
from django.forms import ModelForm, TextInput
from django.forms.models import modelformset_factory

from file_resubmit.admin import AdminResubmitImageWidget

from .models import KolibriDeployment


class KolibriDeploymentForm(ModelForm):
    class Meta:
        model = KolibriDeployment

    def __init__(self, *args, **kwargs):
            super(KolibriDeploymentForm, self).__init__(*args, **kwargs)
            for field_name, field in self.fields.items():
                field.widget.attrs['class'] = 'form-control'

