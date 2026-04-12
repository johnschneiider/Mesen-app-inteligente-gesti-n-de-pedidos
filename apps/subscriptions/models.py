from django.db import models


class SubscriptionPlan(models.Model):
    FREQUENCIES = [
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
    ]
    business = models.ForeignKey(
        'accounts.Business', on_delete=models.CASCADE, related_name='sub_plans'
    )
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    price_cop = models.IntegerField()
    frequency = models.CharField(max_length=10, choices=FREQUENCIES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan de suscripción'
        verbose_name_plural = 'Planes de suscripción'
        ordering = ['price_cop']

    def __str__(self):
        return f'{self.business.name} — {self.name}'


class PlanBenefit(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='benefits')
    text = models.CharField(max_length=120)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Beneficio de plan'

    def __str__(self):
        return self.text


class ClientSubscription(models.Model):
    STATUSES = [
        ('pending', 'Pendiente confirmación'),
        ('active', 'Activa'),
        ('expired', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='client_subs')
    client = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='client_subscriptions'
    )
    status = models.CharField(max_length=10, choices=STATUSES, default='pending')
    starts_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='confirmed_subscriptions'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción de cliente'
        verbose_name_plural = 'Suscripciones de clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client} — {self.plan.name} ({self.status})'
