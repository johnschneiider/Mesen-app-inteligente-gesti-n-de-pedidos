from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View

from apps.accounts.models import Business, DeliveryAddress, User
from apps.menus.models import DailyMenu, MenuRating
from apps.orders.models import Order
from apps.orders.utils import notify_order_update
from apps.store.models import BusinessReview
from apps.subscriptions.models import SubscriptionPlan, ClientSubscription


class StoreView(View):
    template_name = 'store/store.html'

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        now = timezone.now()
        menus = DailyMenu.objects.filter(
            business=business,
            is_active=True,
            valid_from__lte=now,
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        ).prefetch_related('photos', 'ingredients', 'ratings')

        sub_plans = SubscriptionPlan.objects.filter(business=business, is_active=True)

        user_ratings = {}
        if request.user.is_authenticated:
            ratings = MenuRating.objects.filter(
                menu__in=menus, user=request.user
            ).values_list('menu_id', 'score')
            user_ratings = dict(ratings)

        reviews = BusinessReview.objects.filter(business=business).select_related('user')[:30]
        user_review = None
        if request.user.is_authenticated:
            user_review = BusinessReview.objects.filter(business=business, user=request.user).first()

        return render(request, self.template_name, {
            'business': business,
            'menus': menus,
            'sub_plans': sub_plans,
            'user_ratings': user_ratings,
            'reviews': reviews,
            'user_review': user_review,
        })


PAYMENT_OPTIONS = [
    {'val': 'cash',     'icon': '💵', 'label': 'Efectivo'},
    {'val': 'transfer', 'icon': '🔁', 'label': 'Transferencia'},
    {'val': 'card',     'icon': '💳', 'label': 'Tarjeta'},
    {'val': 'fiado',    'icon': '📋', 'label': 'Fiado'},
]

ORDER_TYPES = [
    {'val': 'on_site',  'icon': '🪑', 'label': 'En el lugar'},
    {'val': 'takeaway', 'icon': '🥡', 'label': 'Para llevar'},
    {'val': 'delivery', 'icon': '🛵', 'label': 'Domicilio'},
]


class MenuDetailView(View):
    template_name = 'store/partials/menu_detail.html'

    def _order_ctx(self, user, menu, business, slug):
        saved = list(user.addresses.all()) if user.is_authenticated else []
        otypes = ORDER_TYPES if getattr(business, 'feature_delivery', False) else [o for o in ORDER_TYPES if o['val'] != 'delivery']
        return {
            'menu': menu,
            'business': business,
            'business_slug': slug,
            'payment_options': PAYMENT_OPTIONS,
            'order_types': otypes,
            'consumer': user,
            'saved_addresses': saved,
        }

    def get(self, request, slug, pk):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        menu = get_object_or_404(DailyMenu, pk=pk, business=business, is_active=True)
        # If not authenticated, show quick auth form first
        if not request.user.is_authenticated:
            return render(request, 'store/partials/quick_auth.html', {
                'menu': menu,
                'business': business,
                'business_slug': slug,
            })
        return render(request, self.template_name, self._order_ctx(request.user, menu, business, slug))


class StoreQuickAuthView(View):
    """Handles quick login/register from within the store order modal."""

    def post(self, request, slug, pk):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        menu = get_object_or_404(DailyMenu, pk=pk, business=business, is_active=True)
        action = request.POST.get('auth_action', 'register')

        if action == 'login':
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '').strip()
            user = authenticate(request, phone=phone, password=password)
            if user:
                login(request, user)
            else:
                return render(request, 'store/partials/quick_auth.html', {
                    'menu': menu, 'business': business, 'business_slug': slug,
                    'error': 'Teléfono o contraseña incorrectos.',
                    'tab': 'login',
                })
        else:
            # Register
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '').strip()
            if not full_name or not phone or not password:
                return render(request, 'store/partials/quick_auth.html', {
                    'menu': menu, 'business': business, 'business_slug': slug,
                    'error': 'Completa todos los campos.',
                    'tab': 'register',
                })
            if len(password) < 6:
                return render(request, 'store/partials/quick_auth.html', {
                    'menu': menu, 'business': business, 'business_slug': slug,
                    'error': 'La contraseña debe tener al menos 6 caracteres.',
                    'tab': 'register',
                })
            if User.objects.filter(phone=phone).exists():
                return render(request, 'store/partials/quick_auth.html', {
                    'menu': menu, 'business': business, 'business_slug': slug,
                    'error': 'Ese número ya tiene cuenta. Inicia sesión.',
                    'tab': 'login',
                    'phone_prefill': phone,
                })
            user = User.objects.create_user(phone=phone, password=password, full_name=full_name)
            address_text = request.POST.get('address', '').strip()
            if address_text:
                from apps.accounts.models import DeliveryAddress
                DeliveryAddress.objects.create(user=user, address=address_text, is_default=True)
            login(request, user, backend='apps.accounts.backends.PhoneBackend')

        # After successful auth, show the order form
        saved = list(user.addresses.all())
        otypes = ORDER_TYPES if getattr(business, 'feature_delivery', False) else [o for o in ORDER_TYPES if o['val'] != 'delivery']
        return render(request, 'store/partials/menu_detail.html', {
            'menu': menu,
            'business': business,
            'business_slug': slug,
            'payment_options': PAYMENT_OPTIONS,
            'order_types': otypes,
            'consumer': user,
            'saved_addresses': saved,
        })


class CreateOrderView(View):
    def post(self, request, slug, pk):
        business = get_object_or_404(Business, slug=slug, is_active=True)

        # If not authenticated, return the auth partial via HTMX
        if not request.user.is_authenticated:
            menu = get_object_or_404(DailyMenu, pk=pk, business=business, is_active=True)
            return render(request, 'store/partials/quick_auth.html', {
                'menu': menu, 'business': business, 'business_slug': slug,
                'error': 'Debes iniciar sesión para hacer un pedido.',
            })

        quantity = max(1, int(request.POST.get('quantity', 1)))

        with transaction.atomic():
            menu = DailyMenu.objects.select_for_update().get(
                pk=pk, business=business, is_active=True
            )
            if menu.is_sold_out or menu.units_remaining < quantity:
                if request.headers.get('HX-Request'):
                    return render(request, 'store/partials/order_error.html', {
                        'error': 'Lo sentimos, este menú está agotado.'
                    })
                return redirect('store:store', slug=slug)

            # Update user name from form (always override if provided)
            user = request.user
            submitted_name = request.POST.get('full_name', '').strip()
            if submitted_name and submitted_name != user.full_name:
                user.full_name = submitted_name
                user.save(update_fields=['full_name'])

            order = Order.objects.create(
                business=business,
                client=user,
                menu=menu,
                quantity=quantity,
                unit_price=menu.price,
                total_amount=quantity * menu.price,
                payment_type=request.POST.get('payment_type', 'cash'),
                order_type=request.POST.get('order_type', 'on_site'),
                notes=request.POST.get('notes', ''),
            )
            menu.units_sold += quantity
            menu.save(update_fields=['units_sold'])

        if request.POST.get('order_type') == 'delivery':
            addr_line = request.POST.get('address_line', '').strip()
            if addr_line:
                delivery_addr, _ = DeliveryAddress.objects.get_or_create(
                    user=request.user, address=addr_line,
                    defaults={'label': 'Reciente'}
                )
                order.delivery_address = delivery_addr
                order.save(update_fields=['delivery_address'])

        notify_order_update(business.id, {
            'event': 'new_order',
            'order_id': order.id,
            'order_number': order.order_number,
            'client': user.full_name or user.phone,
            'menu': menu.title,
            'quantity': quantity,
            'total': order.total_amount,
            'status': order.status,
        })

        if request.headers.get('HX-Request'):
            return render(request, 'store/partials/order_success.html', {'order': order})
        return redirect('store:store', slug=slug)


class RateMenuView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        business = get_object_or_404(Business, slug=slug)
        menu = get_object_or_404(DailyMenu, pk=pk, business=business)
        score = int(request.POST.get('score', 5))
        score = max(1, min(5, score))

        MenuRating.objects.update_or_create(
            menu=menu, user=request.user,
            defaults={'score': score},
        )
        if request.headers.get('HX-Request'):
            return render(request, 'store/partials/menu_rating.html', {
                'menu': menu, 'user_score': score
            })
        return redirect('store:store', slug=slug)


class StoreSubscriptionsView(View):
    template_name = 'store/subscriptions.html'

    def get(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        plans = SubscriptionPlan.objects.filter(business=business, is_active=True).prefetch_related('benefits')
        return render(request, self.template_name, {'business': business, 'plans': plans})


class SubscribeView(LoginRequiredMixin, View):
    def post(self, request, slug, pk):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        plan = get_object_or_404(SubscriptionPlan, pk=pk, business=business, is_active=True)

        sub = ClientSubscription.objects.filter(
            plan__business=business, client=request.user, status='active'
        ).first()
        if not sub:
            sub = ClientSubscription.objects.create(plan=plan, client=request.user)

        return render(request, 'store/partials/subscribe_success.html', {
            'plan': plan, 'business': business, 'subscription': sub
        })


class SubmitReviewView(LoginRequiredMixin, View):
    """POST: create or update this user's review for a business."""

    def post(self, request, slug):
        business = get_object_or_404(Business, slug=slug, is_active=True)
        comment = request.POST.get('comment', '').strip()[:600]
        try:
            rating = max(1, min(5, int(request.POST.get('rating', 5))))
        except (ValueError, TypeError):
            rating = 5

        if comment:
            BusinessReview.objects.update_or_create(
                business=business,
                user=request.user,
                defaults={'comment': comment, 'rating': rating},
            )
        return redirect('store:store', slug=slug)
