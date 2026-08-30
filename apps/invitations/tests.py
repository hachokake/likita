from datetime import date, time

from django.test import TestCase

from apps.events.models import Event
from apps.guests.models import Guest
from apps.invitations.models import Invitation
from apps.rsvp.forms import RSVPForm


class InvitationMessageTests(TestCase):
	def test_whatsapp_message_contains_full_public_invitation_url(self):
		invitation = Invitation(
			token='ABCD1234',
			event=Event(
				host_names='Likita',
				name='Ceremonie',
				event_date=date(2026, 1, 1),
				event_time=time(12, 0),
				address='Kinshasa',
			),
			guest=Guest(full_name='Marie'),
		)

		message = invitation.build_whatsapp_message('http://192.168.1.10:8000')

		self.assertIn(
			'http://192.168.1.10:8000/invitations/public/ABCD1234/',
			message,
		)

	def test_rsvp_form_accepts_drink_preference(self):
		form = RSVPForm(
			data={
				'response': 'accepted',
				'companion_count': 0,
				'drink_preference': 'Jus',
				'guest_message': '',
			}
		)

		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['drink_preference'], 'Jus')
