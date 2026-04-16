import uuid
from django.db import models


class Order(models.Model):
    STATUSES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'En preparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]
    PAYMENT_TYPES = [
        ('cash', 'Efectivo'),
        ('transfer', 'Transferencia'),
        ('card', 'Tarjeta'),
        ('fiado', 'Crédito'),
    ]
    ORDER_TYPES = [
        ('on_site', 'En el lugar'),
        ('takeaway', 'Para llevar'),
        ('delivery', 'Domicilio'),
    ]
    VALID_TRANSITIONS = {
        'pending': {'confirmed': 'Confirmar', 'cancelled': 'Cancelar'},
        'confirmed': {'preparing': 'Preparar', 'cancelled': 'Cancelar'},
        'preparing': {'ready': 'Marcar listo'},
        'ready': {'delivered': 'Marcar entregado'},
    }

    business = models.ForeignKey(
        'accounts.Business', on_delete=models.CASCADE, related_name='orders'
    )
    client = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='orders'
    )
    menu = models.ForeignKey(
        'menus.DailyMenu', on_delete=models.PROTECT
    )
    option = models.ForeignKey(
        'menus.MenuOption', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders'
    )
    option_name = models.CharField(max_length=100, blank=True)
    order_number = models.CharField(max_length=8, unique=True, editable=False)
    quantity = models.IntegerField(default=1)
    unit_price = models.IntegerField()
    total_amount = models.IntegerField()

    status = models.CharField(max_length=20, choices=STATUSES, default='pending')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default='cash')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, default='on_site')
    fiado_paid = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    delivery_address = models.ForeignKey(
        'accounts.DeliveryAddress', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='orders'
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.order_number} — {self.client}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = uuid.uuid4().hex[:8].upper()
        if not self.total_amount:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    @property
    def possible_transitions(self):
        return self.VALID_TRANSITIONS.get(self.status, {})

    def get_status_badge_class(self):
        mapping = {
            'pending': 'badge-pendiente',
            'confirmed': 'badge-confirmado',
            'preparing': 'badge-preparacion',
            'ready': 'badge-listo',
            'delivered': 'badge-entregado',
            'cancelled': 'badge-cancelado',
        }
        return mapping.get(self.status, 'badge-pendiente')


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Historial de estado'
        ordering = ['-changed_at']

    def __str__(self):
        return f'#{self.order.order_number}: {self.old_status} → {self.new_status}'
