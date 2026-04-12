from django.db import models


class SupportTicket(models.Model):
    STATUSES = [
        ('open', 'Abierto'),
        ('in_progress', 'En progreso'),
        ('resolved', 'Resuelto'),
    ]
    TYPES = [
        ('technical', 'Técnico'),
        ('billing', 'Facturación'),
        ('feature', 'Solicitud de función'),
        ('other', 'Otro'),
    ]

    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='tickets'
    )
    business = models.ForeignKey(
        'accounts.Business', on_delete=models.CASCADE, null=True, blank=True
    )
    subject = models.CharField(max_length=200)
    ticket_type = models.CharField(max_length=20, choices=TYPES, default='other')
    status = models.CharField(max_length=20, choices=STATUSES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket de soporte'
        verbose_name_plural = 'Tickets de soporte'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} — {self.subject}'


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de ticket'

    def __str__(self):
        return f'Ticket #{self.ticket_id} — {self.author}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.author.is_superadmin and self.ticket.status == 'open':
            self.ticket.status = 'in_progress'
            self.ticket.save(update_fields=['status'])
