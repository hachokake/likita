from django.conf import settings


def app_context(request):
    context = {
        'APP_NAME': settings.APP_NAME,
        'unread_notifications_count': 0,
    }
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        context['unread_notifications_count'] = user.notifications.filter(is_read=False).count()
    return context
