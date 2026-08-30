from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from apps.guests.forms import GuestForm, GuestImportMappingForm, GuestImportUploadForm
from apps.guests.models import Guest
from apps.guests.services import import_guest_rows, parse_guest_import_file

IMPORT_SESSION_KEY = 'guest_import_payload'


class OwnerGuestMixin(LoginRequiredMixin):
    def get_queryset(self):
        queryset = Guest.objects.filter(event__owner=self.request.user).select_related('event', 'invitation', 'rsvp', 'qrcode')
        search_term = self.request.GET.get('q', '').strip()
        if search_term:
            queryset = queryset.filter(
                Q(full_name__icontains=search_term)
                | Q(whatsapp_number__icontains=search_term)
                | Q(category__icontains=search_term)
            )
        return queryset


class GuestListView(OwnerGuestMixin, ListView):
    template_name = 'guests/guest_list.html'
    context_object_name = 'guests'
    paginate_by = 20


class GuestDetailView(OwnerGuestMixin, DetailView):
    template_name = 'guests/guest_detail.html'
    context_object_name = 'guest'


class GuestCreateView(LoginRequiredMixin, CreateView):
    form_class = GuestForm
    template_name = 'guests/guest_form.html'
    success_url = reverse_lazy('guests:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class GuestUpdateView(OwnerGuestMixin, UpdateView):
    form_class = GuestForm
    template_name = 'guests/guest_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('guests:detail', kwargs={'pk': self.object.pk})


class GuestDeleteView(OwnerGuestMixin, DeleteView):
    template_name = 'guests/guest_confirm_delete.html'
    success_url = reverse_lazy('guests:list')


class GuestImportUploadView(LoginRequiredMixin, FormView):
    template_name = 'guests/import_upload.html'
    form_class = GuestImportUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        headers, rows = parse_guest_import_file(form.cleaned_data['file'])
        if not headers or not rows:
            messages.error(self.request, 'Le fichier ne contient aucune donnee exploitable.')
            return redirect('guests:import-upload')

        self.request.session[IMPORT_SESSION_KEY] = {
            'event_id': str(form.cleaned_data['event'].pk),
            'event_name': form.cleaned_data['event'].name,
            'import_mode': form.cleaned_data['import_mode'],
            'headers': headers,
            'rows': rows,
        }
        self.request.session.modified = True
        return redirect('guests:import-map')


class GuestImportMappingView(LoginRequiredMixin, FormView):
    template_name = 'guests/import_map.html'
    form_class = GuestImportMappingForm

    def dispatch(self, request, *args, **kwargs):
        self.payload = request.session.get(IMPORT_SESSION_KEY)
        if not self.payload:
            messages.info(request, 'Chargez d abord un fichier a importer.')
            return redirect('guests:import-upload')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['headers'] = self.payload['headers']
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['headers'] = self.payload['headers']
        context['preview_rows'] = self.payload['rows'][:8]
        context['event_name'] = self.payload['event_name']
        context['import_mode'] = self.payload['import_mode']
        return context

    def form_valid(self, form):
        event = self.request.user.events.get(pk=self.payload['event_id'])
        summary = import_guest_rows(
            event=event,
            rows=self.payload['rows'],
            mapping=form.cleaned_data,
            import_mode=self.payload['import_mode'],
        )
        self.request.session.pop(IMPORT_SESSION_KEY, None)
        if summary['errors']:
            messages.warning(
                self.request,
                f"Import termine: {summary['created']} crees, {summary['updated']} mis a jour, {summary['skipped']} ignores.",
            )
        else:
            messages.success(
                self.request,
                f"Import reussi: {summary['created']} crees, {summary['updated']} mis a jour, {summary['skipped']} ignores.",
            )
        return redirect('guests:list')
