from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from apps.accounts.models import User


class StyledFormMixin:
    default_widget_class = (
        'w-full rounded-md border border-white/15 bg-black/20 px-3.5 py-3 '
        'text-sm text-white placeholder:text-white/45 transition '
        'focus:border-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-500/30'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{self.default_widget_class} {css}'.strip()


class SignUpForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'company_name')


class BosanganiAuthenticationForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(label='Email')