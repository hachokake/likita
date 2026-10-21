from django import forms

from apps.accounts.forms import StyledFormMixin
from apps.rsvp.models import RSVP


DRINK_CHOICES = (
    ('', 'Aucune préférence'),
    ('Eau', 'Eau'),
    ('Jus', 'Jus de fruits'),
    ('Soda', 'Soda'),
    ('Vin', 'Vin'),
    ('Biere', 'Bière'),
    ('Cocktail sans alcool', 'Cocktail sans alcool'),
)


class RSVPForm(StyledFormMixin, forms.ModelForm):
    response = forms.ChoiceField(
        label='Votre réponse',
        choices=(
            (RSVP.Response.ACCEPTED, 'Oui, je serai présent(e)'),
            (RSVP.Response.DECLINED, 'Non, je ne pourrai pas venir'),
        ),
        widget=forms.RadioSelect,
    )

    class Meta:
        model = RSVP
        fields = ('response', 'companion_count', 'drink_preference', 'guest_message')
        labels = {
            'companion_count': "Nombre d'accompagnants",
            'drink_preference': 'Préférence de boisson',
            'guest_message': 'Un mot pour les organisateurs',
        }
        widgets = {
            'drink_preference': forms.Select(choices=DRINK_CHOICES),
            'guest_message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Écrivez votre petit mot ici…'}),
        }

    def __init__(self, *args, **kwargs):
        self.guest = kwargs.pop('guest', None)
        super().__init__(*args, **kwargs)
        self.max_companions = getattr(self.guest, 'allowed_companions', None)
        self.fields['companion_count'].widget.attrs['min'] = 0
        if self.max_companions is not None:
            self.fields['companion_count'].widget.attrs['max'] = self.max_companions
            self.fields['companion_count'].help_text = (
                f"Jusqu'à {self.max_companions} accompagnant{'s' if self.max_companions > 1 else ''} autorisé{'s' if self.max_companions > 1 else ''}."
                if self.max_companions
                else "Cette invitation est strictement personnelle."
            )

    def clean_companion_count(self):
        count = self.cleaned_data.get('companion_count') or 0
        # Un refus n'emmène personne : on ignore la limite dans ce cas.
        if self.data.get('response') == RSVP.Response.DECLINED:
            return 0
        if self.max_companions is not None and count > self.max_companions:
            raise forms.ValidationError(
                f"Votre invitation autorise au maximum {self.max_companions} accompagnant(s)."
            )
        return count

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('response') == RSVP.Response.DECLINED:
            cleaned['companion_count'] = 0
        return cleaned
