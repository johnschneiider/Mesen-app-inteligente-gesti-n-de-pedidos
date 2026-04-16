from datetime import date, timedelta
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views import View

from .forms import PhoneLoginForm, RegisterForm, CreateBusinessForm, ProfileForm, BusinessProfileForm
from .models import User, Business, DeliveryAddress


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('orders:dashboard')
        form = PhoneLoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            user = authenticate(request, phone=phone, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next') or request.POST.get('next', '')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                if user.is_superadmin:
                    return redirect('superadmin:dashboard')
                if user.is_business_owner and user.has_business:
                    return redirect('orders:dashboard')
                return redirect('core:home')
            else:
                form.add_error(None, 'Teléfono o contraseña incorrectos.')
        return render(request, self.template_name, {'form': form})


class LoginModalView(View):
    """HTMX modal para login inline desde la tienda pública."""
    template_name = 'accounts/partials/login_modal.html'

    def get(self, request):
        form = PhoneLoginForm()
        next_url = request.GET.get('next', '')
        return render(request, self.template_name, {'form': form, 'next': next_url})

    def post(self, request):
        form = PhoneLoginForm(request.POST)
        next_url = request.POST.get('next', '')
        if form.is_valid():
            user = authenticate(
                request,
                phone=form.cleaned_data['phone'],
                password=form.cleaned_data['password'],
            )
            if user:
                login(request, user)
                from django.http import HttpResponse
                response = HttpResponse()
                response['HX-Redirect'] = next_url or '/'
                return response
            else:
                form.add_error(None, 'Teléfono o contraseña incorrectos.')
        return render(request, self.template_name, {'form': form, 'next': next_url})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('core:home')


class ValidatePhoneView(View):
    """HTMX endpoint: returns inline HTML fragment for phone validation feedback."""
    def get(self, request):
        from django.http import HttpResponse
        phone = request.GET.get('phone', '').strip()
        mode = request.GET.get('mode', 'register')  # 'register' or 'login'
        if not phone:
            return HttpResponse('')
        if not phone.isdigit() or len(phone) < 7:
            return HttpResponse('<span class="field-hint error">✗ Solo números, mínimo 7 dígitos</span>')
        exists = User.objects.filter(phone=phone).exists()
        if mode == 'login':
            if not exists:
                return HttpResponse('<span class="field-hint error">✗ No encontramos esa cuenta</span>')
            return HttpResponse('<span class="field-hint ok">✓ Cuenta encontrada</span>')
        # register mode
        if exists:
            return HttpResponse('<span class="field-hint error">✗ Este número ya tiene cuenta — inicia sesión</span>')
        if len(phone) != 10:
            return HttpResponse('<span class="field-hint warn">⚠ Los teléfonos colombianos tienen 10 dígitos</span>')
        return HttpResponse('<span class="field-hint ok">✓ Número disponible</span>')


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:home')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='apps.accounts.backends.PhoneBackend')
            messages.success(request, '¡Cuenta creada! Ahora configura tu negocio.')
            return redirect('accounts:upgrade_to_business')
        return render(request, self.template_name, {'form': form})


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def _ctx(self, user_form, biz_form):
        return {'user_form': user_form, 'biz_form': biz_form}

    def get(self, request):
        user_form = ProfileForm(instance=request.user)
        biz_form = BusinessProfileForm(instance=request.user.business) if request.user.has_business else None
        return render(request, self.template_name, self._ctx(user_form, biz_form))

    def post(self, request):
        form_type = request.POST.get('form_type', 'profile')

        if form_type == 'business' and request.user.has_business:
            user_form = ProfileForm(instance=request.user)
            biz_form = BusinessProfileForm(request.POST, request.FILES, instance=request.user.business)
            if biz_form.is_valid():
                biz_form.save()
                messages.success(request, 'Datos del negocio actualizados correctamente.')
                return redirect('accounts:profile')
            return render(request, self.template_name, self._ctx(user_form, biz_form))

        # Default: profile form
        user_form = ProfileForm(request.POST, request.FILES, instance=request.user)
        biz_form = BusinessProfileForm(instance=request.user.business) if request.user.has_business else None
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Información personal actualizada.')
            return redirect('accounts:profile')
        return render(request, self.template_name, self._ctx(user_form, biz_form))


# ══════════════════════════════════════════════════════════
#  CONSUMER ACCOUNT SECTION (/cuenta/)
# ══════════════════════════════════════════════════════════

class ConsumerDashboardView(LoginRequiredMixin, View):
    """Consumer order history and debt summary."""
    template_name = 'cuenta/dashboard.html'
    login_url = '/auth/login/'

    def get(self, request):
        from apps.orders.models import Order
        from django.db.models import Sum

        orders = (
            Order.objects
            .filter(client=request.user)
            .select_related('business', 'menu', 'delivery_address')
            .order_by('-created_at')
        )
        unpaid = orders.filter(is_paid=False).exclude(status='cancelled')
        debt_total = unpaid.aggregate(t=Sum('total_amount'))['t'] or 0
        total_spent = orders.filter(is_paid=True).aggregate(t=Sum('total_amount'))['t'] or 0
        businesses_count = orders.values('business').distinct().count()

        # Restaurantes únicos ordenados por último pedido
        from apps.accounts.models import Business
        business_ids = (
            Order.objects
            .filter(client=request.user)
            .values_list('business_id', flat=True)
            .distinct()
        )
        my_restaurants = Business.objects.filter(id__in=business_ids).only('id', 'name', 'slug', 'logo')

        return render(request, self.template_name, {
            'orders': orders[:30],
            'unpaid': unpaid,
            'debt_total': debt_total,
            'total_spent': total_spent,
            'total_orders': orders.count(),
            'businesses_count': businesses_count,
            'my_restaurants': my_restaurants,
        })


class ConsumerEditView(LoginRequiredMixin, View):
    """Consumer edits their own profile (name, avatar, password)."""
    template_name = 'cuenta/edit.html'
    login_url = '/auth/login/'

    def get(self, request):
        addresses = request.user.addresses.all().order_by('-is_default', 'id')
        return render(request, self.template_name, {'u': request.user, 'addresses': addresses})

    def post(self, request):
        user = request.user
        action = request.POST.get('action', 'profile')

        if action == 'password':
            current = request.POST.get('current_password', '')
            new_pw = request.POST.get('new_password', '')
            confirm_pw = request.POST.get('confirm_password', '')
            addresses = user.addresses.all().order_by('-is_default', 'id')
            if not user.check_password(current):
                messages.error(request, 'La contraseña actual no es correcta.')
                return render(request, self.template_name, {'u': user, 'addresses': addresses})
            if len(new_pw) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
                return render(request, self.template_name, {'u': user, 'addresses': addresses})
            if new_pw != confirm_pw:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, self.template_name, {'u': user, 'addresses': addresses})
            user.set_password(new_pw)
            user.save()
            # Re-login to avoid session invalidation
            login(request, user, backend='apps.accounts.backends.PhoneBackend')
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('accounts:consumer_edit')

        # Default: profile update
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            user.full_name = full_name
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        if request.POST.get('remove_avatar') == '1':
            user.avatar = None
        user.save()
        messages.success(request, 'Perfil actualizado.')
        return redirect('accounts:consumer_edit')


class AddAddressView(LoginRequiredMixin, View):
    login_url = '/auth/login/'

    def post(self, request):
        address_text = request.POST.get('address', '').strip()
        label = request.POST.get('label', '').strip()
        make_default = request.POST.get('is_default') == '1'
        if address_text:
            if make_default:
                request.user.addresses.update(is_default=False)
            addr = DeliveryAddress.objects.create(
                user=request.user,
                address=address_text,
                label=label,
                is_default=make_default or not request.user.addresses.exists(),
            )
            messages.success(request, 'Dirección agregada.')
        return redirect('accounts:consumer_edit')


class DeleteAddressView(LoginRequiredMixin, View):
    login_url = '/auth/login/'

    def post(self, request, pk):
        DeliveryAddress.objects.filter(pk=pk, user=request.user).delete()
        # If none remain with is_default, set first as default
        remaining = request.user.addresses.all().order_by('id')
        if remaining.exists() and not remaining.filter(is_default=True).exists():
            first = remaining.first()
            first.is_default = True
            first.save(update_fields=['is_default'])
        messages.success(request, 'Dirección eliminada.')
        return redirect('accounts:consumer_edit')


class SetDefaultAddressView(LoginRequiredMixin, View):
    login_url = '/auth/login/'

    def post(self, request, pk):
        request.user.addresses.update(is_default=False)
        DeliveryAddress.objects.filter(pk=pk, user=request.user).update(is_default=True)
        return redirect('accounts:consumer_edit')


class UpgradeToBusinessView(LoginRequiredMixin, View):
    template_name = 'accounts/upgrade.html'

    def get(self, request):
        if request.user.has_business:
            return redirect('orders:dashboard')
        return render(request, self.template_name, {'form': CreateBusinessForm()})

    def post(self, request):
        if request.user.has_business:
            return redirect('orders:dashboard')

        form = CreateBusinessForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                business = form.save(commit=False)
                business.owner = request.user

                base_slug = slugify(business.name)
                slug = base_slug
                n = 1
                while Business.objects.filter(slug=slug).exists():
                    slug = f'{base_slug}-{n}'
                    n += 1
                business.slug = slug
                business.save()

                request.user.role = 'BUSINESS_OWNER'
                request.user.save(update_fields=['role'])

                from apps.billing.models import SaaSSubscription
                SaaSSubscription.objects.create(
                    business=business,
                    plan='starter',
                    amount_cop=0,
                    starts_at=date.today(),
                    expires_at=date.today() + timedelta(days=30),
                    status='active',
                )

            messages.success(request, f'¡Negocio "{business.name}" creado exitosamente!')
            return redirect('orders:dashboard')

        return render(request, self.template_name, {'form': form})
