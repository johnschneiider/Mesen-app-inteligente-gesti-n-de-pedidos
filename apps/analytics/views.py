from datetime import timedelta
from django.core.cache import cache as redis_cache
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.core.mixins import PlanRequiredMixin
from apps.orders.models import Order

_ANALYTICS_CACHE_TTL = 120  # 2 min


class AnalyticsDashboardView(PlanRequiredMixin, View):
    template_name = 'analytics/dashboard.html'
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        business = request.user.business
        days = int(request.GET.get('days', 7))
        since = timezone.now() - timedelta(days=days)

        cache_key = f'analytics_dash_{business.pk}_{days}'
        result = redis_cache.get(cache_key)
        if result is None:
            agg = Order.objects.filter(
                business=business, created_at__gte=since
            ).aggregate(t=Sum('total_amount'), c=Count('id'))
            result = {
                'total_revenue': agg['t'] or 0,
                'total_orders': agg['c'] or 0,
            }
            redis_cache.set(cache_key, result, _ANALYTICS_CACHE_TTL)

        return render(request, self.template_name, {
            'days': days,
            'total_revenue': result['total_revenue'],
            'total_orders': result['total_orders'],
        })


class SalesChartDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        days = int(request.GET.get('days', 7))
        business = request.user.business
        since = timezone.now() - timedelta(days=days)

        cache_key = f'analytics_sales_{business.pk}_{days}'
        payload = redis_cache.get(cache_key)
        if payload is None:
            data = (
                Order.objects
                .filter(business=business, created_at__gte=since)
                .annotate(day=TruncDay('created_at'))
                .values('day')
                .annotate(total=Sum('total_amount'), count=Count('id'))
                .order_by('day')
            )
            payload = {
                'labels': [d['day'].strftime('%d %b') for d in data],
                'sales': [d['total'] for d in data],
                'orders': [d['count'] for d in data],
            }
            redis_cache.set(cache_key, payload, _ANALYTICS_CACHE_TTL)
        return JsonResponse(payload)


class TopClientsDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        business = request.user.business

        cache_key = f'analytics_top_{business.pk}'
        payload = redis_cache.get(cache_key)
        if payload is None:
            data = (
                Order.objects
                .filter(business=business)
                .values('client__full_name', 'client__phone')
                .annotate(total=Sum('total_amount'), orders=Count('id'))
                .order_by('-total')[:10]
            )
            payload = {'clients': list(data)}
            redis_cache.set(cache_key, payload, _ANALYTICS_CACHE_TTL)
        return JsonResponse(payload)


class PaymentRatioDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        business = request.user.business

        cache_key = f'analytics_ratio_{business.pk}'
        payload = redis_cache.get(cache_key)
        if payload is None:
            # Single combined query instead of 2 separate
            agg = Order.objects.filter(business=business).values('payment_type').annotate(
                t=Sum('total_amount'), c=Count('id')
            )
            result = {row['payment_type']: row for row in agg}
            contado = result.get('contado', {})
            fiado = result.get('fiado', {})
            payload = {
                'contado_total': contado.get('t') or 0,
                'contado_count': contado.get('c') or 0,
                'fiado_total': fiado.get('t') or 0,
                'fiado_count': fiado.get('c') or 0,
            }
            redis_cache.set(cache_key, payload, _ANALYTICS_CACHE_TTL)
        return JsonResponse(payload)
