from apps.notifications.models import Notification


def create_notification(*, user, kind, title, body, event=None, guest=None):
    return Notification.objects.create(
        user=user,
        kind=kind,
        title=title,
        body=body,
        event=event,
        guest=guest,
    )