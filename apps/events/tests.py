import shutil
import tempfile
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.events.forms import EventForm
from apps.events.models import Event
from apps.guests.models import Guest
from apps.notifications.models import Notification
from apps.rsvp.models import RSVP
from apps.scanner.models import ScanLog


TEST_MEDIA_ROOT = tempfile.mkdtemp()


class EventFormLabelTests(SimpleTestCase):
    def test_event_form_labels_are_in_french(self):
        self.assertEqual(
            {name: field.label for name, field in EventForm().fields.items()},
            {
                'name': 'Nom de l’événement',
                'event_type': 'Type d’événement',
                'description': 'Description',
                'host_names': 'Noms des hôtes',
                'cover_image': 'Image de couverture',
                'event_date': 'Date de l’événement',
                'event_time': 'Heure de l’événement',
                'address': 'Adresse',
                'google_maps_url': 'Lien Google Maps',
                'detailed_program': 'Programme détaillé',
                'dress_code': 'Code vestimentaire',
                'welcome_message': 'Message de bienvenue',
                'rsvp_deadline': 'Date limite de réponse',
                'max_guests': 'Nombre maximal d’invités',
                'background_music': 'Musique de fond',
                'allow_multiple_entries': 'Autoriser plusieurs entrées',
            },
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EventDashboardViewTests(TestCase):
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
            name='Soirée Élégance',
            host_names='Alice et Marc',
            event_date=date(2027, 5, 22),
            event_time=time(18, 30),
            address='Le Grand Salon',
        )
        self.accepted_guest = Guest.objects.create(
            event=self.event,
            full_name='Jean Dupont',
            whatsapp_number='+243810000001',
        )
        self.declined_guest = Guest.objects.create(
            event=self.event,
            full_name='Marie Dupont',
            whatsapp_number='+243810000002',
        )
        Guest.objects.create(
            event=self.event,
            full_name='Paul Dupont',
            whatsapp_number='+243810000003',
        )
        accepted_rsvp = self.accepted_guest.rsvp
        accepted_rsvp.response = RSVP.Response.ACCEPTED
        accepted_rsvp.save()
        declined_rsvp = self.declined_guest.rsvp
        declined_rsvp.response = RSVP.Response.DECLINED
        declined_rsvp.save()
        ScanLog.objects.create(
            event=self.event,
            guest=self.accepted_guest,
            qr_code=self.accepted_guest.qrcode,
            status=ScanLog.ScanStatus.ALLOWED,
        )
        ScanLog.objects.create(
            event=self.event,
            guest=self.accepted_guest,
            qr_code=self.accepted_guest.qrcode,
            status=ScanLog.ScanStatus.ALLOWED,
        )
        ScanLog.objects.create(
            event=self.event,
            status=ScanLog.ScanStatus.INVALID,
        )
        Notification.objects.create(
            user=self.owner,
            event=self.event,
            guest=self.accepted_guest,
            kind=Notification.Kind.RSVP_ACCEPTED,
            title='Présence confirmée',
            body='Jean Dupont a confirmé sa présence.',
        )
        self.dashboard_url = reverse('events:dashboard', kwargs={'slug': self.event.slug})

    def test_owner_sees_exact_event_statistics(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Soirée Élégance')
        self.assertContains(response, 'Présence confirmée')
        self.assertEqual(
            response.context['metrics'],
            {
                'total_guests': 3,
                'accepted_guests': 1,
                'declined_guests': 1,
                'pending_guests': 1,
                'confirmation_rate': 33.3,
                'total_qr_codes': 3,
                'qr_codes_scanned': 1,
                'valid_scans': 2,
                'unique_admissions': 1,
                'confirmed_not_arrived': 0,
                'arrival_rate': 100.0,
                'response_breakdown': (
                    {
                        'label': 'Confirmées',
                        'count': 1,
                        'percentage': 33.3,
                        'color': 'bg-emerald-400',
                    },
                    {
                        'label': 'Refusées',
                        'count': 1,
                        'percentage': 33.3,
                        'color': 'bg-rose-400',
                    },
                    {
                        'label': 'En attente',
                        'count': 1,
                        'percentage': 33.3,
                        'color': 'bg-amber-300',
                    },
                ),
            },
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.dashboard_url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.dashboard_url}")

    def test_other_user_cannot_access_event_dashboard(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 404)

    def test_event_without_guests_has_zero_rates(self):
        empty_event = Event.objects.create(
            owner=self.owner,
            name='Événement vide',
            host_names='Alice',
            event_date=date(2027, 6, 1),
            event_time=time(12, 0),
            address='Kinshasa',
        )
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse('events:dashboard', kwargs={'slug': empty_event.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['metrics']['total_guests'], 0)
        self.assertEqual(response.context['metrics']['confirmation_rate'], 0)
        self.assertEqual(response.context['metrics']['arrival_rate'], 0)
