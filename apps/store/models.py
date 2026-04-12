from django.db import models
from django.utils import timezone

from apps.accounts.models import Business, User


class BusinessReview(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_reviews')
    comment = models.TextField(max_length=600)
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        unique_together = [('business', 'user')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.business} ({self.rating}★)'
