from django import forms
from .models import User, Resume
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'location', 'experience_level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.role == 'employer':
            self.fields.pop('experience_level', None)
        if 'role' in self.fields:
            self.fields['role'].widget.attrs['readonly'] = True

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    pass 