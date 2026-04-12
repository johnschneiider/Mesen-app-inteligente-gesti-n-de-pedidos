from django.db import models
from django.utils import timezone


class SaaSSubscription(models.Model):
    PLANS = [
        ('starter', 'Starter'),
        ('professional', 'Pro+'),
        ('enterprise', 'Enterprise'),
    ]
    STATUSES = [
        ('active', 'Activa'),
        ('expiring_soon', 'Por vencer'),
        ('expired', 'Vencida'),
        ('suspended', 'Suspendida'),
    ]
    PLAN_AMOUNTS = {
        'starter': 299000,
        'professional': 599000,
        'enterprise': 999000,
    }

    PLAN_LEVELS = {'starter': 0, 'professional': 1, 'enterprise': 2}

    business = models.OneToOneField(
        'accounts.Business', on_delete=models.CASCADE, related_name='saas_subscription'
    )
    plan = models.CharField(max_length=20, choices=PLANS, default='starter')
    amount_cop = models.IntegerField(default=299000)
    starts_at = models.DateField()
    expires_at = models.DateField()
    status = models.CharField(max_length=20, choices=STATUSES, default='active')
    bold_payment_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscripción SaaS'
        verbose_name_plural = 'Suscripciones SaaS'

    def __str__(self):
        return f'{self.business.name} — {self.get_plan_display()}'

    def days_until_expiry(self):
        return (self.expires_at - timezone.now().date()).days

    @property
    def plan_level(self):
        """0=Starter, 1=Professional, 2=Enterprise"""
        return self.PLAN_LEVELS.get(self.plan, 0)

    @property
    def is_active_subscription(self):
        return self.status in ('active', 'expiring_soon')

    def update_status(self):
        days = self.days_until_expiry()
        if days < 0:
            self.status = 'expired'
        elif days <= 7:
            self.status = 'expiring_soon'
        else:
            self.status = 'active'
        self.save(update_fields=['status'])


class PaymentRecord(models.Model):
    subscription = models.ForeignKey(
        SaaSSubscription, on_delete=models.CASCADE, related_name='payments'
    )
    amount_cop = models.IntegerField()
    paid_at = models.DateField()
    confirmed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Pago registrado'
        verbose_name_plural = 'Pagos registrados'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.subscription.business.name} — ${self.amount_cop:,} ({self.paid_at})'
