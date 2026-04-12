from django import forms
from .models import DailyMenu, MenuIngredient


class DailyMenuForm(forms.ModelForm):
    class Meta:
        model = DailyMenu
        fields = ['title', 'description', 'price', 'max_units', 'valid_from', 'valid_until', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ej: Almuerzo ejecutivo'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del menú…'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Precio en COP (ej: 15000)'}),
            'max_units': forms.NumberInput(attrs={'placeholder': 'Unidades disponibles'}),
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valid_until'].required = False
        from django.utils import timezone
        if self.instance and self.instance.pk:
            if self.instance.valid_from:
                self.initial['valid_from'] = timezone.localtime(self.instance.valid_from).strftime('%Y-%m-%dT%H:%M')
            if self.instance.valid_until:
                self.initial['valid_until'] = timezone.localtime(self.instance.valid_until).strftime('%Y-%m-%dT%H:%M')
        else:
            # Pre-fill with current local time so the menu is visible immediately
            self.initial['valid_from'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')


class MenuIngredientForm(forms.ModelForm):
    class Meta:
        model = MenuIngredient
        fields = ['name', 'grams']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: Arroz blanco', 'autocomplete': 'off'}),
            'grams': forms.NumberInput(attrs={'placeholder': 'g', 'min': '1', 'style': 'width:70px;'}),
        }


class MenuPhotoForm(forms.Form):
    image = forms.ImageField()
