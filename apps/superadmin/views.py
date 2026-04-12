from datetime import date, timedelta
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View

from apps.accounts.models import User, Business
from apps.billing.models import SaaSSubscription, PaymentRecord
from apps.core.mixins import SuperAdminRequiredMixin
from apps.orders.models import Order
from apps.support.models import SupportTicket, TicketMessage
from apps.support.forms import TicketMessageForm


class SuperAdminDashboardView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/dashboard.html'

    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'businesses_active': Business.objects.filter(is_active=True, is_suspended=False).count(),
            'clients_total': User.objects.filter(role='CLIENT').count(),
            'orders_total': Order.objects.count(),
            'saas_revenue_month': SaaSSubscription.objects.filter(
                starts_at__gte=month_start
            ).aggregate(t=Sum('amount_cop'))['t'] or 0,
            'tickets_open': SupportTicket.objects.filter(status='open').count(),
            'expiring_soon': SaaSSubscription.objects.filter(
                expires_at__lte=today + timedelta(days=7),
                expires_at__gte=today,
                status='active',
            ).count(),
        }

        recent_businesses = Business.objects.select_related(
            'owner', 'saas_subscription'
        ).order_by('-created_at')[:10]

        return render(request, self.template_name, {
            'stats': stats,
            'recent_businesses': recent_businesses,
        })


class BusinessListView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/business_list.html'

    def get(self, request):
        businesses = Business.objects.select_related(
            'owner', 'saas_subscription'
        ).order_by('-created_at')
        return render(request, self.template_name, {'businesses': businesses})


class BusinessDetailView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/business_detail.html'

    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        sub = getattr(business, 'saas_subscription', None)
        orders = Order.objects.filter(business=business).order_by('-created_at')[:20]
        return render(request, self.template_name, {
            'business': business,
            'sub': sub,
            'orders': orders,
        })


class EditSubscriptionView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        sub, _ = SaaSSubscription.objects.get_or_create(
            business=business,
            defaults={
                'plan': 'starter',
                'amount_cop': 299000,
                'starts_at': date.today(),
                'expires_at': date.today() + timedelta(days=30),
            }
        )
        plan = request.POST.get('plan', sub.plan)
        sub.plan = plan
        sub.amount_cop = SaaSSubscription.PLAN_AMOUNTS.get(plan, 299000)
        expires_str = request.POST.get('expires_at')
        if expires_str:
            sub.expires_at = date.fromisoformat(expires_str)
        sub.notes = request.POST.get('notes', sub.notes)
        sub.save()
        sub.update_status()

        if request.POST.get('confirm_payment'):
            PaymentRecord.objects.create(
                subscription=sub,
                amount_cop=sub.amount_cop,
                paid_at=date.today(),
                confirmed_by=request.user,
                notes=request.POST.get('payment_notes', ''),
            )

        messages.success(request, 'Suscripción actualizada.')
        return redirect('superadmin:business_detail', pk=pk)


class EditFeaturesView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        business.feature_analytics = 'feature_analytics' in request.POST
        business.feature_whatsapp = 'feature_whatsapp' in request.POST
        business.feature_multi_branch = 'feature_multi_branch' in request.POST
        business.feature_api = 'feature_api' in request.POST
        business.save(update_fields=[
            'feature_analytics', 'feature_whatsapp',
            'feature_multi_branch', 'feature_api',
        ])
        messages.success(request, 'Features actualizados.')
        return redirect('superadmin:business_detail', pk=pk)


class SuspendBusinessView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        action = request.POST.get('action', 'suspend')
        if action == 'suspend':
            business.is_suspended = True
            sub = getattr(business, 'saas_subscription', None)
            if sub:
                sub.status = 'suspended'
                sub.save(update_fields=['status'])
        else:
            business.is_suspended = False
        business.save(update_fields=['is_suspended'])
        messages.success(request, 'Estado del negocio actualizado.')
        return redirect('superadmin:business_detail', pk=pk)


class TicketListView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/ticket_list.html'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        tickets = SupportTicket.objects.select_related('created_by', 'business')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        return render(request, self.template_name, {
            'tickets': tickets,
            'status_filter': status_filter,
        })


class TicketDetailView(SuperAdminRequiredMixin, View):
    template_name = 'superadmin/ticket_detail.html'

    def get(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk)
        return render(request, self.template_name, {
            'ticket': ticket,
            'messages_list': ticket.messages.select_related('author').all(),
            'form': TicketMessageForm(),
        })

    def post(self, request, pk):
        ticket = get_object_or_404(SupportTicket, pk=pk)
        form = TicketMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.author = request.user
            msg.save()
            return redirect('superadmin:ticket_detail', pk=pk)
        return render(request, self.template_name, {
            'ticket': ticket,
            'messages_list': ticket.messages.all(),
            'form': form,
        })
