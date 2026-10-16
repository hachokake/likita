import shutil
import tempfile
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.events.models import Event
from apps.guests.models import Guest
from apps.rsvp.forms import RSVPForm
from apps.rsvp.models import RSVP


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PublicRSVPUpdateViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        owner = get_user_model().objects.create_user(
            email='organisateur@example.com',
            password='test-password',
        )
        self.event = Event.objects.create(
            owner=owner,
            name='Soirée Élégance',
            host_names='Alice et Marc',
            event_date=date(2027, 5, 22),
            event_time=time(18, 30),
            address='Le Grand Salon',
        )
        self.guest = Guest.objects.create(
            event=self.event,
            full_name='Jean Dupont',
            whatsapp_number='+243810000000',
        )
        self.invitation = self.guest.invitation

    def test_accepted_response_redirects_to_personal_invitation_pass(self):
        response = self.client.post(
            reverse('rsvp:respond', kwargs={'token': self.invitation.token}),
            {
                'response': RSVP.Response.ACCEPTED,
                'companion_count': 0,
                'drink_preference': 'Eau',
                'guest_message': 'Merci.',
            },
        )

        self.assertRedirects(
            response,
            (
                reverse('invitations:public', kwargs={'token': self.invitation.token})
                + '?response_saved=1#invitation-pass'
            ),
            fetch_redirect_response=False,
        )

        page = self.client.get(
            reverse('invitations:public', kwargs={'token': self.invitation.token}),
            {'response_saved': '1'},
        )
        self.assertContains(page, 'id="invitation-pass"')
        self.assertNotContains(page, "Voici votre carte d'invitation personnelle.")
        self.assertContains(page, 'Jean Dupont')
        self.assertContains(page, self.guest.qrcode.image.url)

        reloaded_page = self.client.get(
            reverse('invitations:public', kwargs={'token': self.invitation.token}),
            {'response_saved': '1'},
        )
        self.assertNotContains(reloaded_page, 'id="invitation-pass"')

    def test_previously_accepted_guest_must_submit_form_to_see_pass(self):
        rsvp = self.guest.rsvp
        rsvp.response = RSVP.Response.ACCEPTED
        rsvp.save()
        invitation_url = reverse('invitations:public', kwargs={'token': self.invitation.token})

        for query in ({}, {'response_saved': '1'}):
            with self.subTest(query=query):
                page = self.client.get(invitation_url, query)
                self.assertNotContains(page, 'id="invitation-pass"')
                self.assertFalse(page.context['response_saved'])

    def test_invalid_submission_does_not_reveal_pass(self):
        rsvp = self.guest.rsvp
        rsvp.response = RSVP.Response.ACCEPTED
        rsvp.save()
        response = self.client.post(
            reverse('rsvp:respond', kwargs={'token': self.invitation.token}),
            {'response': RSVP.Response.ACCEPTED, 'companion_count': -1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

        page = self.client.get(
            reverse('invitations:public', kwargs={'token': self.invitation.token}),
            {'response_saved': '1'},
        )
        self.assertNotContains(page, 'id="invitation-pass"')

    def test_declined_response_confirms_save_without_revealing_pass(self):
        response = self.client.post(
            reverse('rsvp:respond', kwargs={'token': self.invitation.token}),
            {'response': RSVP.Response.DECLINED, 'companion_count': 0},
            follow=True,
        )
        self.assertContains(response, 'Votre réponse a bien été enregistrée.')
        self.assertNotContains(response, 'id="invitation-pass"')

    def test_pending_guest_does_not_see_invitation_pass(self):
        page = self.client.get(
            reverse('invitations:public', kwargs={'token': self.invitation.token})
        )

        self.assertNotContains(page, 'id="invitation-pass"')

    def test_rsvp_form_labels_are_in_french(self):
        self.assertEqual(
            {name: field.label for name, field in RSVPForm().fields.items()},
            {
                'response': 'Votre réponse',
                'companion_count': "Nombre d'accompagnateurs",
                'drink_preference': 'Préférence de boisson',
                'guest_message': 'Message aux organisateurs',
            },
        )
