from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.accounts.models import User
from apps.adminpanel.models import ActivityLog
from apps.events.models import Event
from apps.guests.models import Guest
from apps.scanner.models import ScanLog


class StaffOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.info(self.request, "Connectez-vous avec un compte administrateur pour acceder a cette page.")
        admin_login_url = f"{reverse('admin:login')}?next={self.request.get_full_path()}"
        return HttpResponseRedirect(admin_login_url)


def create_activity(actor, action, target_type='', target_identifier='', metadata=None):
    ActivityLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_identifier=target_identifier,
        metadata=metadata or {},
    )


class AdminDashboardView(StaffOnlyMixin, TemplateView):
    template_name = 'adminpanel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.all()
        events = Event.objects.all()
        guests = Guest.objects.all()
        scans = ScanLog.objects.all()

        context['admin_tab'] = 'dashboard'
        context['global_stats'] = {
            'users': users.count(),
            'staff': users.filter(is_staff=True).count(),
            'suspended_users': users.filter(is_suspended=True).count(),
            'events': events.count(),
            'published_events': events.filter(status=Event.Status.PUBLISHED).count(),
            'guests': guests.count(),
            'scans': scans.count(),
            'successful_scans': scans.filter(status=ScanLog.ScanStatus.ALLOWED).count(),
        }
        context['recent_activity'] = ActivityLog.objects.select_related('actor')[:10]
        context['top_accounts'] = User.objects.annotate(total_events=Count('events')).order_by('-total_events')[:8]
        context['status_mix'] = Guest.objects.values('status').annotate(total=Count('id')).order_by('-total')
        context['scan_mix'] = ScanLog.objects.values('status').annotate(total=Count('id')).order_by('-total')
        context['recent_users'] = users.order_by('-date_joined')[:8]
        context['recent_events'] = events.select_related('owner').order_by('-created_at')[:8]
        return context


class AdminUserListView(StaffOnlyMixin, ListView):
    model = User
    template_name = 'adminpanel/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.annotate(
            total_events=Count('events', distinct=True),
            total_guests=Count('events__guests', distinct=True),
        ).order_by('-date_joined')

        search = self.request.GET.get('q', '').strip()
        tier = self.request.GET.get('tier', '').strip()
        state = self.request.GET.get('state', '').strip()

        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(company_name__icontains=search)
                | Q(phone_number__icontains=search)
            )

        if tier:
            queryset = queryset.filter(subscription_tier=tier)

        if state == 'actif':
            queryset = queryset.filter(is_active=True, is_suspended=False)
        elif state == 'suspendu':
            queryset = queryset.filter(is_suspended=True)
        elif state == 'staff':
            queryset = queryset.filter(is_staff=True)
        elif state == 'superadmin':
            queryset = queryset.filter(is_superuser=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin_tab'] = 'users'
        context['search'] = self.request.GET.get('q', '').strip()
        context['selected_tier'] = self.request.GET.get('tier', '').strip()
        context['selected_state'] = self.request.GET.get('state', '').strip()
        context['tiers'] = User.SubscriptionTier.choices
        context['state_options'] = [
            ('actif', 'Actif'),
            ('suspendu', 'Suspendu'),
            ('staff', 'Staff'),
            ('superadmin', 'Super administrateur'),
        ]
        return context


class AdminUserDetailView(StaffOnlyMixin, DetailView):
    model = User
    template_name = 'adminpanel/user_detail.html'
    context_object_name = 'target_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.object
        context['admin_tab'] = 'users'
        context['recent_events'] = (
            Event.objects.filter(owner=target_user)
            .annotate(total_guests=Count('guests'))
            .order_by('-created_at')[:8]
        )
        context['event_count'] = Event.objects.filter(owner=target_user).count()
        context['guest_count'] = Guest.objects.filter(event__owner=target_user).count()
        context['scan_count'] = ScanLog.objects.filter(event__owner=target_user).count()
        return context


class AdminUserActionView(StaffOnlyMixin, View):
    def post(self, request, pk, action):
        target_user = get_object_or_404(User, pk=pk)
        next_url = request.POST.get('next') or reverse('adminpanel:user-detail', kwargs={'pk': target_user.pk})

        update_fields = ['updated_at']
        action_label = ''

        if action == 'suspendre':
            target_user.is_suspended = True
            action_label = 'Utilisateur suspendu'
            update_fields.append('is_suspended')
        elif action == 'reactiver':
            target_user.is_suspended = False
            action_label = 'Utilisateur reactive'
            update_fields.append('is_suspended')
        elif action == 'promouvoir-staff':
            target_user.is_staff = True
            action_label = 'Utilisateur promu staff'
            update_fields.append('is_staff')
        elif action == 'retirer-staff':
            if target_user == request.user:
                messages.error(request, 'Vous ne pouvez pas retirer votre propre acces staff.')
                return HttpResponseRedirect(next_url)
            target_user.is_staff = False
            action_label = 'Acces staff retire'
            update_fields.append('is_staff')
        elif action == 'activer-compte':
            target_user.is_active = True
            action_label = 'Compte active'
            update_fields.append('is_active')
        elif action == 'desactiver-compte':
            if target_user == request.user:
                messages.error(request, 'Vous ne pouvez pas desactiver votre propre compte.')
                return HttpResponseRedirect(next_url)
            target_user.is_active = False
            action_label = 'Compte desactive'
            update_fields.append('is_active')
        elif action == 'promouvoir-superadmin':
            if not request.user.is_superuser:
                messages.error(request, 'Action reservee au super administrateur.')
                return HttpResponseRedirect(next_url)
            target_user.is_superuser = True
            target_user.is_staff = True
            action_label = 'Utilisateur promu super administrateur'
            update_fields.extend(['is_superuser', 'is_staff'])
        elif action == 'retirer-superadmin':
            if not request.user.is_superuser:
                messages.error(request, 'Action reservee au super administrateur.')
                return HttpResponseRedirect(next_url)
            if target_user == request.user:
                messages.error(request, 'Vous ne pouvez pas retirer votre propre role super administrateur.')
                return HttpResponseRedirect(next_url)
            target_user.is_superuser = False
            action_label = 'Role super administrateur retire'
            update_fields.append('is_superuser')
        else:
            messages.error(request, 'Action inconnue.')
            return HttpResponseRedirect(next_url)

        target_user.save(update_fields=update_fields)
        create_activity(
            actor=request.user,
            action=action_label,
            target_type='user',
            target_identifier=target_user.email,
            metadata={'action': action},
        )
        messages.success(request, f'{action_label} pour {target_user.email}.')
        return HttpResponseRedirect(next_url)


class AdminEventListView(StaffOnlyMixin, ListView):
    model = Event
    template_name = 'adminpanel/events.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Event.objects.select_related('owner')
            .annotate(
                total_guests=Count('guests', distinct=True),
                total_scans=Count('scan_logs', distinct=True),
            )
            .order_by('-created_at')
        )

        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        owner = self.request.GET.get('owner', '').strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(address__icontains=search)
                | Q(owner__email__icontains=search)
                | Q(host_names__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        if owner:
            queryset = queryset.filter(owner_id=owner)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin_tab'] = 'events'
        context['search'] = self.request.GET.get('q', '').strip()
        context['selected_status'] = self.request.GET.get('status', '').strip()
        context['selected_owner'] = self.request.GET.get('owner', '').strip()
        context['status_choices'] = Event.Status.choices
        context['owner_choices'] = User.objects.order_by('email').values('id', 'email')[:200]
        return context


class AdminEventDetailView(StaffOnlyMixin, DetailView):
    model = Event
    template_name = 'adminpanel/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        context['admin_tab'] = 'events'
        context['guest_count'] = Guest.objects.filter(event=event).count()
        context['scan_count'] = ScanLog.objects.filter(event=event).count()
        context['recent_guests'] = Guest.objects.filter(event=event).order_by('-created_at')[:10]
        context['recent_scans'] = ScanLog.objects.filter(event=event).select_related('guest', 'scanned_by').order_by('-scanned_at')[:10]
        return context


class AdminEventActionView(StaffOnlyMixin, View):
    def post(self, request, pk, action):
        event = get_object_or_404(Event.objects.select_related('owner'), pk=pk)
        next_url = request.POST.get('next') or reverse('adminpanel:event-detail', kwargs={'pk': event.pk})

        if action == 'publier':
            event.status = Event.Status.PUBLISHED
            if not event.published_at:
                event.published_at = timezone.now()
            event.save(update_fields=['status', 'published_at', 'updated_at'])
            action_label = 'Evenement publie'
        elif action == 'archiver':
            event.status = Event.Status.ARCHIVED
            event.save(update_fields=['status', 'updated_at'])
            action_label = 'Evenement archive'
        elif action == 'brouillon':
            event.status = Event.Status.DRAFT
            event.save(update_fields=['status', 'updated_at'])
            action_label = 'Evenement repasse en brouillon'
        elif action == 'supprimer':
            event_name = event.name
            event.delete()
            create_activity(
                actor=request.user,
                action='Evenement supprime',
                target_type='event',
                target_identifier=event_name,
                metadata={'action': action},
            )
            messages.success(request, f'Evenement {event_name} supprime.')
            return HttpResponseRedirect(reverse('adminpanel:events'))
        else:
            messages.error(request, 'Action inconnue.')
            return HttpResponseRedirect(next_url)

        create_activity(
            actor=request.user,
            action=action_label,
            target_type='event',
            target_identifier=event.name,
            metadata={'action': action, 'event_id': str(event.pk)},
        )
        messages.success(request, f'{action_label} : {event.name}.')
        return HttpResponseRedirect(next_url)

