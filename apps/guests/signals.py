from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.guests.models import Guest
from apps.invitations.models import Invitation
from apps.qrmanager.models import QRCode
from apps.qrmanager.services import generate_qr_image
from apps.rsvp.models import RSVP


@receiver(post_save, sender=Guest)
def provision_guest_records(sender, instance, created, **kwargs):
    if not created:
        return
    Invitation.objects.get_or_create(guest=instance, defaults={'event': instance.event})
    RSVP.objects.get_or_create(guest=instance, defaults={'event': instance.event})
    qr_code, _ = QRCode.objects.get_or_create(guest=instance, defaults={'event': instance.event})
    if not qr_code.image:
        generate_qr_image(qr_code)