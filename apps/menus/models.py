from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg


class DailyMenu(models.Model):
    business = models.ForeignKey(
        'accounts.Business', on_delete=models.CASCADE, related_name='menus'
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    max_units = models.IntegerField(default=50)
    units_sold = models.IntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Menú del día'
        verbose_name_plural = 'Menús del día'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.business.name} — {self.title}'

    @property
    def is_sold_out(self):
        return self.units_sold >= self.max_units

    @property
    def units_remaining(self):
        return max(0, self.max_units - self.units_sold)

    @property
    def avg_rating(self):
        r = self.ratings.aggregate(avg=Avg('score'))['avg']
        return round(r, 1) if r else None

    @property
    def units_available(self):
        """Alias for max_units — used in templates."""
        return self.max_units

    @property
    def main_photo(self):
        return self.photos.first()

    @property
    def featured_photo(self):
        return self.photos.first()


class MenuPhoto(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='menus/')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Foto de menú'

    def __str__(self):
        return f'Foto {self.order} — {self.menu.title}'


class MenuIngredient(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=80)
    grams = models.IntegerField(null=True, blank=True, help_text='Cantidad en gramos (opcional)')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Ingrediente'

    def __str__(self):
        return self.name


class MenuOption(models.Model):
    """Variante de precio de un menú (ej: "Con sopa" $13000, "Solo bandeja" $10000)."""
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='options')
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Opción de precio'
        verbose_name_plural = 'Opciones de precio'

    def __str__(self):
        return f'{self.name} — ${self.price:,}'


class MenuRating(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['menu', 'user']
        verbose_name = 'Calificación'

    def __str__(self):
        return f'{self.user} — {self.menu.title} ({self.score}★)'


class MenuLike(models.Model):
    menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['menu', 'user']
