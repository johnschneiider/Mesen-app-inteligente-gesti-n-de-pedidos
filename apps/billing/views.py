from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from apps.core.mixins import BusinessOwnerRequiredMixin
from .models import SaaSSubscription


class BillingDetailView(BusinessOwnerRequiredMixin, View):
    template_name = 'billing/detail.html'

    def get(self, request):
        sub = getattr(request.user.business, 'saas_subscription', None)
        payments = sub.payments.all() if sub else []
        return render(request, self.template_name, {'sub': sub, 'payments': payments})


class SubscriptionExpiredView(LoginRequiredMixin, View):
    template_name = 'billing/expired.html'

    def get(self, request):
        sub = getattr(request.user.business, 'saas_subscription', None)
        return render(request, self.template_name, {'sub': sub})
