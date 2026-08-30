from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


def generate_qr_image(qr_code):
    payload = str(qr_code.token)
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    qr_code.image.save(f'{qr_code.token}.png', ContentFile(buffer.getvalue()), save=True)
    return qr_code