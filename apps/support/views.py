from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from apps.core.mixins import BusinessOwnerRequiredMixin
from .models import SupportTicket, TicketMessage
from .forms import TicketForm, TicketMessageForm


class TicketListView(BusinessOwnerRequiredMixin, View):
    template_name = 'support/list.html'

    def get(self, request):
        tickets = SupportTicket.objects.filter(
            created_by=request.user
        ).prefetch_related('messages')
        return render(request, self.template_name, {
            'tickets': tickets,
            'form': TicketForm(),
        })

    def post(self, request):
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            if request.user.has_business:
                ticket.business = request.user.business
            ticket.save()
            return redirect('support:detail', pk=ticket.pk)
        tickets = SupportTicket.objects.filter(created_by=request.user)
        return render(request, self.template_name, {'tickets': tickets, 'form': form})


class TicketDetailView(LoginRequiredMixin, View):
    template_name = 'support/detail.html'

    def get(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk, created_by=request.user)
        return render(request, self.template_name, {
            'ticket': ticket,
            'messages': ticket.messages.all(),
            'form': TicketMessageForm(),
        })

    def post(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk, created_by=request.user)
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.author = request.user
            msg.save()
            return redirect('support:detail', pk=pk)
        return render(request, self.template_name, {
            'ticket': ticket,
            'messages': ticket.messages.all(),
            'form': form,
        })


class CloseTicketView(LoginRequiredMixin, View):
    def post(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk, created_by=request.user)
        ticket.status = 'resolved'
        ticket.save(update_fields=['status'])
        return redirect('support:list')
