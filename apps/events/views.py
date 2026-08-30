from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.events.forms import EventForm
from apps.events.models import Event, EventProgram, Gallery, Theme


class OwnerEventMixin(LoginRequiredMixin):
    def get_queryset(self):
        return (
            Event.objects.filter(owner=self.request.user)
            .select_related('theme')
            .prefetch_related(
                Prefetch('program_items', queryset=EventProgram.objects.order_by('sort_order', 'start_at')),
                Prefetch('gallery_items', queryset=Gallery.objects.order_by('sort_order', 'created_at')),
            )
            .annotate(guest_count=Count('guests'))
        )


class EventListView(OwnerEventMixin, ListView):
    template_name = 'events/event_list.html'
    context_object_name = 'events'


class EventDetailView(OwnerEventMixin, DetailView):
    template_name = 'events/event_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'event'


class EventCreateView(LoginRequiredMixin, CreateView):
    form_class = EventForm
    template_name = 'events/event_form.html'
    success_url = reverse_lazy('events:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        Theme.objects.get_or_create(event=self.object)
        return response


class EventUpdateView(OwnerEventMixin, UpdateView):
    form_class = EventForm
    template_name = 'events/event_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_success_url(self):
        return reverse('events:detail', kwargs={'slug': self.object.slug})


class EventStatusUpdateView(LoginRequiredMixin, View):
    status = Event.Status.DRAFT

    def post(self, request, slug):
        event = get_object_or_404(Event, owner=request.user, slug=slug)
        event.status = self.status
        event.save(update_fields=['status', 'updated_at'])
        return HttpResponseRedirect(reverse('events:detail', kwargs={'slug': event.slug}))


class EventPublishView(EventStatusUpdateView):
    status = Event.Status.PUBLISHED


class EventArchiveView(EventStatusUpdateView):
    status = Event.Status.ARCHIVED
