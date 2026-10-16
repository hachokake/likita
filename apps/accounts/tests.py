from django.test import SimpleTestCase

from apps.accounts.forms import BosanganiAuthenticationForm, SignUpForm


class AccountFormLabelTests(SimpleTestCase):
    def test_signup_and_login_labels_are_in_french(self):
        self.assertEqual(
            {name: field.label for name, field in SignUpForm().fields.items()},
            {
                'first_name': 'Prénom',
                'last_name': 'Nom',
                'email': 'Adresse e-mail',
                'phone_number': 'Numéro de téléphone',
                'company_name': 'Nom de l’entreprise',
                'password1': 'Mot de passe',
                'password2': 'Confirmation du mot de passe',
            },
        )
        self.assertEqual(
            {name: field.label for name, field in BosanganiAuthenticationForm().fields.items()},
            {
                'username': 'Adresse e-mail',
                'password': 'Mot de passe',
            },
        )
