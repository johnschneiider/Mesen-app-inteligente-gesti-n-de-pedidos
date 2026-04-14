from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render


class BusinessOwnerRequiredMixin(LoginRequiredMixin):
    """Solo dueños de negocio activo pueden acceder."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_business_owner or not request.user.has_business:
            return redirect('accounts:upgrade_to_business')
        # business already loaded by SubscriptionCheckMiddleware → no extra query
        business = request.user.__dict__.get('business') or request.user.business
        if business.is_suspended:
            return render(request, 'core/business_suspended.html')
        return super().dispatch(request, *args, **kwargs)


class PlanRequiredMixin(BusinessOwnerRequiredMixin):
    """Verifica que el plan del negocio sea suficiente para acceder a la vista."""
    min_plan_level = 1  # Pro+ por defecto
    feature_name = 'esta función'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_business_owner or not request.user.has_business:
            return redirect('accounts:upgrade_to_business')
        business = request.user.__dict__.get('business') or request.user.business
        if business.is_suspended:
            return render(request, 'core/business_suspended.html')
        if business.current_plan_level < self.min_plan_level:
            plan_name = 'Pro+' if self.min_plan_level == 1 else 'Enterprise'
            return render(request, 'core/feature_disabled.html', {
                'plan_required': plan_name,
                'feature_name': self.feature_name,
            })
        from django.views import View
        return View.dispatch(self, request, *args, **kwargs)


class FeatureRequiredMixin:
    """Verifica que el negocio tenga el feature flag activado (legacy)."""
    feature_flag = None

    def dispatch(self, request, *args, **kwargs):
        business = request.user.business
        if not getattr(business, self.feature_flag, False):
            return render(request, 'core/feature_disabled.html', {'flag': self.feature_flag})
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superadmin:
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)
