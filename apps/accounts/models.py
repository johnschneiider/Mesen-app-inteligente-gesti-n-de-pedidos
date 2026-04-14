from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('El número de teléfono es obligatorio')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPERADMIN')
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ('CLIENT', 'Cliente'),
        ('BUSINESS_OWNER', 'Dueño de negocio'),
        ('SUPERADMIN', 'Superadmin'),
    ]

    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=20, choices=ROLES, default='CLIENT')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.full_name or self.phone}'

    @property
    def is_business_owner(self):
        return self.role == 'BUSINESS_OWNER'

    @property
    def is_superadmin(self):
        return self.role == 'SUPERADMIN'

    @property
    def has_business(self):
        # Avoid triggering a DB query: check __dict__ first (cached by middleware),
        # then fields_cache (set by select_related), before falling back to DB.
        if 'business' in self.__dict__:
            return True
        cache = self.__dict__.get('_state', None)
        if cache and hasattr(cache, 'fields_cache') and 'business' in cache.fields_cache:
            return True
        try:
            return self.business is not None
        except self.__class__.business.RelatedObjectDoesNotExist:
            return False

    def get_initials(self):
        if self.full_name:
            parts = self.full_name.strip().split()
            if len(parts) >= 2:
                return (parts[0][0] + parts[1][0]).upper()
            return parts[0][:2].upper()
        return self.phone[:2].upper()


class Business(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=80, default='Colombia')
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Feature flags (controlled by superadmin)
    feature_analytics = models.BooleanField(default=False)
    feature_whatsapp = models.BooleanField(default=False)
    feature_multi_branch = models.BooleanField(default=False)
    feature_api = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'

    def __str__(self):
        return self.name

    def get_store_url(self):
        return f'/tienda/{self.slug}/'

    @property
    def current_plan_level(self):
        """Returns 0=Starter, 1=Professional, 2=Enterprise. 0 if no active subscription."""
        try:
            sub = self.saas_subscription
            if sub.is_active_subscription:
                return sub.plan_level
        except Exception:
            pass
        return 0

    def can_use(self, feature):
        """Check if business plan allows a feature.
        Features: 'analytics', 'subscriptions', 'clients' → Professional (1)
                  'whatsapp', 'multi_branch', 'api'      → Enterprise (2)
        """
        _feature_plan = {
            'analytics': 1,
            'subscriptions': 1,
            'clients': 1,
            'whatsapp': 2,
            'multi_branch': 2,
            'api': 2,
        }
        return self.current_plan_level >= _feature_plan.get(feature, 99)


class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=200)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Dirección de entrega'
        verbose_name_plural = 'Direcciones de entrega'

    def __str__(self):
        return f'{self.user} — {self.address}'
