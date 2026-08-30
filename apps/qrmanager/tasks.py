from celery import shared_task

from apps.qrmanager.models import QRCode
from apps.qrmanager.services import generate_qr_image


@shared_task
def build_qr_image(qr_code_id):
    qr_code = QRCode.objects.get(pk=qr_code_id)
    generate_qr_image(qr_code)
    return str(qr_code.image)