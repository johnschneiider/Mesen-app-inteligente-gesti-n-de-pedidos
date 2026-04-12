from datetime import date, timedelta
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View

from apps.core.mixins import BusinessOwnerRequiredMixin, PlanRequiredMixin
from .models import SubscriptionPlan, PlanBenefit, ClientSubscription
from .forms import SubscriptionPlanForm, PlanBenefitForm


class SubscriptionListView(PlanRequiredMixin, View):
    template_name = 'subscriptions/list.html'
    min_plan_level = 1
    feature_name = 'Suscripciones de clientes'

    def get(self, request):
        business = request.user.business
        plans = SubscriptionPlan.objects.filter(business=business).prefetch_related('benefits', 'client_subs')
        pending_subs = ClientSubscription.objects.filter(
            plan__business=business, status='pending'
        ).select_related('client', 'plan')
        return render(request, self.template_name, {
            'plans': plans,
            'pending_subs': pending_subs,
        })


class SubscriptionPlanCreateView(BusinessOwnerRequiredMixin, View):
    template_name = 'subscriptions/plan_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': SubscriptionPlanForm(), 'action': 'Crear'})

    def post(self, request):
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.business = request.user.business
            plan.save()
            return redirect('subscriptions:list')
        return render(request, self.template_name, {'form': form, 'action': 'Crear'})


class SubscriptionPlanUpdateView(BusinessOwnerRequiredMixin, View):
    template_name = 'subscriptions/plan_form.html'

    def get(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk, business=request.user.business)
        return render(request, self.template_name, {
            'form': SubscriptionPlanForm(instance=plan), 'plan': plan, 'action': 'Editar'
        })

    def post(self, request, pk):
        plan = get_object_or_404(SubscriptionPlan, pk=pk, business=request.user.business)
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect('subscriptions:list')
        return render(request, self.template_name, {'form': form, 'plan': plan, 'action': 'Editar'})


class ConfirmClientSubscriptionView(BusinessOwnerRequiredMixin, View):
    def post(self, request, pk):
        sub = get_object_or_404(ClientSubscription, pk=pk, plan__business=request.user.business)
        freq = sub.plan.frequency
        today = date.today()
        if freq == 'weekly':
            expires = today + timedelta(weeks=1)
        elif freq == 'biweekly':
            expires = today + timedelta(weeks=2)
        else:
            expires = today + timedelta(days=30)

        sub.status = 'active'
        sub.starts_at = today
        sub.expires_at = expires
        sub.confirmed_by = request.user
        sub.confirmed_at = timezone.now()
        sub.save()

        if request.headers.get('HX-Request'):
            return render(request, 'subscriptions/partials/sub_row.html', {'sub': sub})
        return redirect('subscriptions:list')
