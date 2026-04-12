from django import forms
from .models import SupportTicket, TicketMessage


class TicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'ticket_type']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': '¿En qué podemos ayudarte?'}),
        }


class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe tu mensaje…'}),
        }
