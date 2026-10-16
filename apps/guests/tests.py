import shutil
import tempfile
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.events.models import Event
from apps.guests.forms import GuestForm, GuestImportUploadForm
from apps.guests.models import Guest
from apps.rsvp.models import RSVP


TEST_MEDIA_ROOT = tempfile.mkdtemp()


class GuestFormLabelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='organisateur@example.com',
            password='test-password',
        )

    def test_guest_form_labels_are_in_french(self):
        self.assertEqual(
            {name: field.label for name, field in GuestForm(user=self.user).fields.items()},
            {
                'event': 'Événement',
                'full_name': 'Nom complet',
                'whatsapp_number': 'Numéro WhatsApp',
                'email': 'Adresse e-mail',
                'category': 'Catégorie',
                'allowed_companions': 'Nombre d’accompagnateurs autorisés',
                'reserved_table': 'Table réservée',
                'notes': 'Notes',
            },
        )

    def test_guest_import_form_labels_are_in_french(self):
        self.assertEqual(
            {name: field.label for name, field in GuestImportUploadForm(user=self.user).fields.items()},
            {
                'event': 'Événement',
                'file': 'Fichier à importer',
                'import_mode': 'Mode d’importation',
            },
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class GuestListFilteringTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            email='organisateur@example.com',
            password='test-password',
        )
        self.other_user = get_user_model().objects.create_user(
            email='autre@example.com',
            password='test-password',
        )
        self.event = Event.objects.create(
            owner=self.owner,
            name='Mariage Dupont',
            host_names='Alice et Marc',
            event_date=date(2027, 5, 22),
            event_time=time(18, 30),
            address='Le Grand Salon',
        )
        self.other_event = Event.objects.create(
            owner=self.other_user,
            name='Événement privé',
            host_names='Autre utilisateur',
            event_date=date(2027, 6, 1),
            event_time=time(12, 0),
            address='Kinshasa',
        )
        self.accepted_guest = Guest.objects.create(
            event=self.event,
            full_name='Marie Martin',
            whatsapp_number='+243810000001',
        )
        Guest.objects.create(
            event=self.event,
            full_name='Paul Martin',
            whatsapp_number='+243810000002',
        )
        Guest.objects.create(
            event=self.other_event,
            full_name='Invité privé',
            whatsapp_number='+243810000003',
        )
        rsvp = self.accepted_guest.rsvp
        rsvp.response = RSVP.Response.ACCEPTED
        rsvp.save()

    def test_event_response_and_search_filters_are_applied(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse('guests:list'),
            {
                'event': self.event.pk,
                'response': RSVP.Response.ACCEPTED,
                'q': 'Marie',
            },
        )

        self.assertContains(response, 'Marie Martin')
        self.assertNotContains(response, 'Paul Martin')
        self.assertNotContains(response, 'Invité privé')
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_other_users_event_filter_returns_no_guests(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse('guests:list'),
            {'event': self.other_event.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 0)
