from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.events.models import Event


class EventForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'name',
            'event_type',
            'description',
            'host_names',
            'cover_image',
            'event_date',
            'event_time',
            'address',
            'google_maps_url',
            'detailed_program',
            'dress_code',
            'welcome_message',
            'rsvp_deadline',
            'max_guests',
            'background_music',
            'allow_multiple_entries',
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'type': 'time'}),
            'rsvp_deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'detailed_program': forms.Textarea(attrs={'rows': 5}),
            'welcome_message': forms.Textarea(attrs={'rows': 4}),
        }