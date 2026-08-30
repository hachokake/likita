from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.rsvp.models import RSVP


class RSVPForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = RSVP
        fields = ('response', 'companion_count', 'drink_preference', 'guest_message')
        widgets = {
            'drink_preference': forms.Select(
                choices=(
                    ('', 'Aucune preference'),
                    ('Eau', 'Eau'),
                    ('Jus', 'Jus de fruits'),
                    ('Soda', 'Soda'),
                    ('Vin', 'Vin'),
                    ('Biere', 'Biere'),
                    ('Cocktail sans alcool', 'Cocktail sans alcool'),
                )
            ),
            'guest_message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Laisser un message aux organisateurs'}),
        }