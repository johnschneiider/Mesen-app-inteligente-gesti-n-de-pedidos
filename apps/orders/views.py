from django.db.models import Sum, Count, Q, Prefetch
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from apps.accounts.models import DeliveryAddress
from apps.core.mixins import BusinessOwnerRequiredMixin, PlanRequiredMixin
from .models import Order, OrderStatusHistory
from .utils import notify_order_update


class DashboardView(BusinessOwnerRequiredMixin, View):
    template_name = 'orders/dashboard.html'

    def get(self, request):
        business = request.user.business
        from django.utils import timezone
        today = timezone.localtime(timezone.now()).date()

        orders_today = Order.objects.filter(business=business, created_at__date=today)
        recent_orders = Order.objects.filter(business=business).select_related('client', 'menu')[:10]

        # Pedidos esta semana por día
        from django.db.models.functions import TruncDay
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        weekly_data = (
            Order.objects.filter(business=business, created_at__gte=week_ago)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Top clientes
        top_clients = (
            Order.objects.filter(business=business)
            .values('client__full_name', 'client__phone', 'client__id')
            .annotate(total=Sum('total_amount'), order_count=Count('id'))
            .order_by('-total')[:5]
        )

        # Fiado pendiente
        fiado_pending = Order.objects.filter(
            business=business, payment_type='fiado', is_paid=False
        )
        fiado_total = fiado_pending.aggregate(t=Sum('total_amount'))['t'] or 0
        fiado_clients = fiado_pending.values('client__id').distinct().count()

        stats = {
            'orders_today': orders_today.count(),
            'revenue_today': orders_today.aggregate(t=Sum('total_amount'))['t'] or 0,
            'preparing_count': Order.objects.filter(business=business, status='preparing').count(),
            'fiado_total': fiado_total,
            'fiado_clients': fiado_clients,
        }

        # Gráfico barras semanal
        days_labels = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        week_counts = [0] * 7
        for entry in weekly_data:
            dow = entry['day'].weekday()
            week_counts[dow] = entry['count']
        weekly_total = sum(week_counts)

        context = {
            'stats': stats,
            'recent_orders': recent_orders,
            'top_clients': top_clients,
            'week_counts': week_counts,
            'weekly_total': weekly_total,
            'days_labels': days_labels,
        }
        return render(request, self.template_name, context)


class OrderListView(BusinessOwnerRequiredMixin, View):
    template_name = 'orders/list.html'

    def get(self, request):
        from django.core.paginator import Paginator
        business = request.user.business
        status_filter = request.GET.get('status', '')
        payment_filter = request.GET.get('payment_type', '')
        orders = Order.objects.filter(business=business).select_related('client', 'menu', 'delivery_address').prefetch_related(
            Prefetch('client__addresses', queryset=DeliveryAddress.objects.filter(is_default=True), to_attr='default_addresses')
        ).order_by('-created_at')
        if status_filter:
            orders = orders.filter(status=status_filter)
        if payment_filter:
            orders = orders.filter(payment_type=payment_filter)
        paginator = Paginator(orders, 25)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        pending_count = Order.objects.filter(business=business, status='pending').count()
        return render(request, self.template_name, {
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1,
            'pending_count': pending_count,
        })


class LiveOrdersView(BusinessOwnerRequiredMixin, View):
    template_name = 'orders/live.html'

    def get(self, request):
        business = request.user.business
        active_orders = Order.objects.filter(
            business=business,
            status__in=['pending', 'confirmed', 'preparing', 'ready'],
        ).select_related('client', 'menu')
        return render(request, self.template_name, {'active_orders': active_orders})


class ChangeOrderStatusView(BusinessOwnerRequiredMixin, View):
    VALID_TRANSITIONS = {
        'pending': ['confirmed', 'cancelled'],
        'confirmed': ['preparing', 'cancelled'],
        'preparing': ['ready'],
        'ready': ['delivered'],
    }

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, business=request.user.business)
        new_status = request.POST.get('status')
        allowed = self.VALID_TRANSITIONS.get(order.status, [])

        if new_status not in allowed:
            return HttpResponse('Transición inválida', status=400)

        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])

        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
        )

        notify_order_update(request.user.business.id, {
            'event': 'status_change',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': new_status,
            'new_status_display': order.get_status_display(),
        })

        if request.headers.get('HX-Request'):
            return render(request, 'orders/partials/order_row.html', {'order': order})
        return redirect('orders:live')


class MarkOrderPaidView(BusinessOwnerRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, business=request.user.business)
        order.is_paid = True
        order.save(update_fields=['is_paid', 'updated_at'])

        if request.headers.get('HX-Request'):
            return render(request, 'orders/partials/order_row.html', {'order': order})
        return redirect('orders:list')


class ConfirmAllPendingView(BusinessOwnerRequiredMixin, View):
    def post(self, request):
        business = request.user.business
        pending = Order.objects.filter(business=business, status='pending')
        count = pending.count()
        for order in pending:
            OrderStatusHistory.objects.create(
                order=order,
                old_status='pending',
                new_status='confirmed',
                changed_by=request.user,
            )
        pending.update(status='confirmed')
        notify_order_update(business.id, {
            'event': 'bulk_confirm',
            'count': count,
        })
        if request.headers.get('HX-Request'):
            orders = Order.objects.filter(business=business).select_related('client', 'menu').order_by('-created_at')[:25]
            return render(request, 'orders/partials/order_row.html', {'orders': orders})
        from django.contrib import messages
        messages.success(request, f'{count} pedido(s) confirmado(s).')
        return redirect('orders:list')


class ClientListView(PlanRequiredMixin, View):
    template_name = 'orders/clients.html'
    min_plan_level = 1
    feature_name = 'Lista de clientes'

    def get(self, request):
        business = request.user.business
        clients = (
            Order.objects.filter(business=business)
            .values(
                'client__id', 'client__full_name', 'client__phone',
            )
            .annotate(
                order_count=Count('id'),
                total_spent=Sum('total_amount'),
                fiado_pending=Sum(
                    'total_amount',
                    filter=Q(payment_type='fiado', is_paid=False)
                ),
            )
            .order_by('-total_spent')
        )
        return render(request, self.template_name, {'clients': clients})


class OrderSearchView(BusinessOwnerRequiredMixin, View):
    template_name = 'orders/partials/search_results.html'

    def get(self, request):
        q = request.GET.get('q', '').strip()
        orders = []
        if q:
            orders = Order.objects.filter(
                business=request.user.business
            ).filter(
                Q(order_number__icontains=q) |
                Q(client__full_name__icontains=q) |
                Q(client__phone__icontains=q)
            ).select_related('client', 'menu', 'delivery_address').prefetch_related(
                Prefetch('client__addresses', queryset=DeliveryAddress.objects.filter(is_default=True), to_attr='default_addresses')
            )[:8]
        return render(request, self.template_name, {'orders': orders, 'q': q})
