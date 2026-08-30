"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

handler404 = 'apps.core.views.error_404'
handler500 = 'apps.core.views.error_500'

urlpatterns = [
    path('admin/', RedirectView.as_view(pattern_name='adminpanel:dashboard', permanent=False)),
    path('admin-django-interne/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('events/', include('apps.events.urls')),
    path('guests/', include('apps.guests.urls')),
    path('invitations/', include('apps.invitations.urls')),
    path('rsvp/', include('apps.rsvp.urls')),
    path('scanner/', include('apps.scanner.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('administration/', include('apps.adminpanel.urls')),
    path('api/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
