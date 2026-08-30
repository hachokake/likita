from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.forms import StyledFormMixin
from apps.events.models import Event
from apps.guests.models import Guest


class GuestForm(StyledFormMixin, forms.ModelForm):
    event = forms.ModelChoiceField(queryset=Event.objects.none())

    class Meta:
        model = Guest
        fields = [
            'event',
            'full_name',
            'whatsapp_number',
            'email',
            'category',
            'allowed_companions',
            'reserved_table',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(owner=user).order_by('-event_date')


class GuestImportUploadForm(StyledFormMixin, forms.Form):
    IMPORT_MODE_CHOICES = (
        ('create_only', 'Ignorer les doublons'),
        ('upsert', 'Mettre a jour les doublons'),
    )

    event = forms.ModelChoiceField(queryset=Event.objects.none())
    file = forms.FileField()
    import_mode = forms.ChoiceField(choices=IMPORT_MODE_CHOICES, initial='create_only')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(owner=user).order_by('-event_date')

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        allowed_extensions = ('.csv', '.xlsx', '.xlsm')
        if not uploaded.name.lower().endswith(allowed_extensions):
            raise ValidationError('Formats acceptes: CSV, XLSX ou XLSM.')
        return uploaded


class GuestImportMappingForm(StyledFormMixin, forms.Form):
    FIELD_LABELS = {
        'full_name': 'Nom complet',
        'whatsapp_number': 'Numero WhatsApp',
        'email': 'Email',
        'category': 'Categorie',
        'allowed_companions': 'Nombre d accompagnants',
        'reserved_table': 'Table reservee',
        'notes': 'Notes',
    }
    REQUIRED_FIELDS = {'full_name', 'whatsapp_number'}

    def __init__(self, *args, **kwargs):
        headers = kwargs.pop('headers')
        super().__init__(*args, **kwargs)
        choices = [('', 'Ne pas importer')] + [(header, header) for header in headers]
        for field_name, label in self.FIELD_LABELS.items():
            self.fields[field_name] = forms.ChoiceField(
                choices=choices,
                required=field_name in self.REQUIRED_FIELDS,
                label=label,
            )

    def clean(self):
        cleaned_data = super().clean()
        selected_columns = [value for value in cleaned_data.values() if value]
        if len(selected_columns) != len(set(selected_columns)):
            raise ValidationError('Une meme colonne ne peut pas etre mappee plusieurs fois.')
        return cleaned_data