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
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.CheckboxSelectMultiple)):
                continue
            css = widget.attrs.get('class', '')
            classes = f'{self.default_widget_class} {css}'
            if isinstance(widget, forms.ClearableFileInput):
                classes += ' file-input'
            widget.attrs['class'] = classes.strip()


class SignUpForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'company_name')
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse e-mail',
            'phone_number': 'Numéro de téléphone',
            'company_name': 'Nom de l’entreprise',
        }


class BosanganiAuthenticationForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(
        label='Adresse e-mail',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'vous@exemple.com'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password', 'placeholder': '••••••••'})