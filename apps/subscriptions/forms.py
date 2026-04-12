from django import forms
from .models import SubscriptionPlan, PlanBenefit


class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = ['name', 'description', 'price_cop', 'frequency', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej: Plan Ejecutivo Mensual'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'price_cop': forms.NumberInput(attrs={'placeholder': 'Ej: 250000'}),
        }


class PlanBenefitForm(forms.ModelForm):
    class Meta:
        model = PlanBenefit
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Ej: Almuerzo diario incluido'}),
        }
