from datetime import timedelta
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.core.mixins import PlanRequiredMixin
from apps.orders.models import Order


class AnalyticsDashboardView(PlanRequiredMixin, View):
    template_name = 'analytics/dashboard.html'
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        business = request.user.business
        days = int(request.GET.get('days', 7))
        since = timezone.now() - timedelta(days=days)
        total_revenue = Order.objects.filter(
            business=business, created_at__gte=since
        ).aggregate(t=Sum('total_amount'))['t'] or 0
        total_orders = Order.objects.filter(
            business=business, created_at__gte=since
        ).count()
        return render(request, self.template_name, {
            'days': days,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
        })


class SalesChartDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'

    def get(self, request):
        days = int(request.GET.get('days', 7))
        business = request.user.business
        since = timezone.now() - timedelta(days=days)

        data = (
            Order.objects
            .filter(business=business, created_at__gte=since)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum('total_amount'), count=Count('id'))
            .order_by('day')
        )
        return JsonResponse({
            'labels': [d['day'].strftime('%d %b') for d in data],
            'sales': [d['total'] for d in data],
            'orders': [d['count'] for d in data],
        })


class TopClientsDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'
    feature_flag = 'feature_analytics'

    def get(self, request):
        business = request.user.business
        data = (
            Order.objects
            .filter(business=business)
            .values('client__full_name', 'client__phone')
            .annotate(total=Sum('total_amount'), orders=Count('id'))
            .order_by('-total')[:10]
        )
        return JsonResponse({'clients': list(data)})


class PaymentRatioDataView(PlanRequiredMixin, View):
    min_plan_level = 1
    feature_name = 'Analítica'
    feature_flag = 'feature_analytics'

    def get(self, request):
        business = request.user.business
        contado = Order.objects.filter(business=business, payment_type='contado').aggregate(
            t=Sum('total_amount'), c=Count('id')
        )
        fiado = Order.objects.filter(business=business, payment_type='fiado').aggregate(
            t=Sum('total_amount'), c=Count('id')
        )
        return JsonResponse({
            'contado_total': contado['t'] or 0,
            'contado_count': contado['c'] or 0,
            'fiado_total': fiado['t'] or 0,
            'fiado_count': fiado['c'] or 0,
        })
