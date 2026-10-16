import shutil
import tempfile
from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.events.models import Event
from apps.guests.models import Guest
from apps.scanner.models import ScanLog
from apps.scanner.services import process_scan


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ScanProcessingTests(TestCase):
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
        self.guest = Guest.objects.create(
            event=self.event,
            full_name='Jean Dupont',
            whatsapp_number='+243810000000',
        )

    def test_non_owner_cannot_validate_another_organizers_qr_code(self):
        result = process_scan(self.guest.qrcode.token, user=self.other_user)

        self.assertFalse(result['ok'])
        self.assertEqual(result['message'], 'QR non autorisé')
        self.assertIsNone(result['guest'])
        self.guest.refresh_from_db()
        self.guest.qrcode.refresh_from_db()
        self.assertEqual(self.guest.status, Guest.Status.PENDING)
        self.assertEqual(self.guest.qrcode.scan_count, 0)
        self.assertEqual(result['log'].status, ScanLog.ScanStatus.INVALID)

    def test_repeated_scan_does_not_admit_guest_twice(self):
        first_result = process_scan(self.guest.qrcode.token, user=self.owner)
        repeated_result = process_scan(self.guest.qrcode.token, user=self.owner)

        self.assertTrue(first_result['ok'])
        self.assertFalse(repeated_result['ok'])
        self.assertEqual(repeated_result['log'].status, ScanLog.ScanStatus.REUSED)
        self.assertEqual(
            ScanLog.objects.filter(
                event=self.event,
                status=ScanLog.ScanStatus.ALLOWED,
            ).count(),
            1,
        )
