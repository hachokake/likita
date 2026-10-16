import shutil
import tempfile
from datetime import date, time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.events.models import Event
from apps.guests.models import Guest
from apps.invitations.models import Invitation
from apps.invitations.services import DeliveryResult, send_qr_image_via_provider
from apps.rsvp.forms import RSVPForm
from apps.rsvp.models import RSVP


TEST_MEDIA_ROOT = tempfile.mkdtemp()


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


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SendInvitationViewTests(TestCase):
	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

	def setUp(self):
		self.owner = get_user_model().objects.create_user(
			email='organisateur@example.com',
			password='test-password',
		)
		self.event = Event.objects.create(
			owner=self.owner,
			name='Cérémonie',
			host_names='Likita',
			event_date=date(2026, 1, 1),
			event_time=time(12, 0),
			address='Kinshasa',
		)
		self.guest = Guest.objects.create(
			event=self.event,
			full_name='Marie',
			whatsapp_number='+243810000000',
		)

	@override_settings(APP_BASE_URL='https://invitation-test.example.com')
	@patch('apps.invitations.views.send_invitation_via_provider')
	def test_send_uses_configured_public_base_url(self, send_invitation):
		send_invitation.return_value = DeliveryResult(
			success=True,
			fallback_url='https://api.whatsapp.com/send',
			provider=Invitation.Provider.MANUAL,
		)
		self.client.force_login(self.owner)

		response = self.client.get(
			reverse('invitations:send', kwargs={'token': self.guest.invitation.token})
		)

		self.assertRedirects(
			response,
			'https://api.whatsapp.com/send',
			fetch_redirect_response=False,
		)
		send_invitation.assert_called_once_with(
			self.guest.invitation,
			base_url='https://invitation-test.example.com',
		)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class QRImageDeliveryTests(TestCase):
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
			name='Cérémonie',
			host_names='Likita',
			event_date=date(2026, 1, 1),
			event_time=time(12, 0),
			address='Kinshasa',
		)
		self.guest = Guest.objects.create(
			event=self.event,
			full_name='Marie',
			whatsapp_number='+243810000000',
		)
		self.invitation = self.guest.invitation

	def test_qr_image_is_not_sent_before_rsvp_confirmation(self):
		result = send_qr_image_via_provider(self.invitation)

		self.assertFalse(result.success)
		self.assertEqual(
			result.error,
			"Le QR code ne peut etre envoye qu'apres confirmation de presence.",
		)

	@override_settings(
		WHATSAPP_PROVIDER=Invitation.Provider.WHATSAPP_CLOUD,
		WHATSAPP_ACCESS_TOKEN='test-token',
		WHATSAPP_PHONE_NUMBER_ID='123456',
	)
	@patch('apps.invitations.services.requests.post')
	def test_cloud_provider_sends_the_existing_qr_image(self, post):
		rsvp = self.guest.rsvp
		rsvp.response = RSVP.Response.ACCEPTED
		rsvp.save()
		upload_response = type(
			'Response',
			(),
			{'status_code': 200, 'text': '', 'json': lambda self: {'id': 'media-id'}},
		)()
		send_response = type(
			'Response',
			(),
			{
				'status_code': 200,
				'text': '',
				'json': lambda self: {'messages': [{'id': 'message-id'}]},
			},
		)()
		post.side_effect = [upload_response, send_response]

		result = send_qr_image_via_provider(self.invitation)

		self.assertTrue(result.success)
		self.assertEqual(result.message_id, 'message-id')
		self.assertEqual(post.call_count, 2)
		self.assertTrue(post.call_args_list[0].args[0].endswith('/media'))
		self.assertEqual(post.call_args_list[0].kwargs['data']['type'], 'image/png')
		self.assertEqual(post.call_args_list[1].kwargs['json']['type'], 'image')
		self.assertEqual(post.call_args_list[1].kwargs['json']['image'], {'id': 'media-id'})

	def test_other_user_cannot_send_qr_image(self):
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('invitations:send-qr', kwargs={'token': self.invitation.token})
		)

		self.assertEqual(response.status_code, 404)
