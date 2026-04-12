from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.text import slugify
from .models import User, Business


class PhoneLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Número de teléfono',
            'autocomplete': 'tel',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password',
        })
    )


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña (mínimo 6 caracteres)'}),
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'}),
    )

    class Meta:
        model = User
        fields = ['phone', 'full_name']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Este número ya está registrado.')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw2 = cleaned_data.get('password_confirm')
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class CreateBusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'description', 'phone', 'address', 'city', 'logo', 'cover_image']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nombre de tu restaurante'}),
            'description': forms.Textarea(attrs={'placeholder': 'Descripción breve…', 'rows': 3}),
            'phone': forms.TextInput(attrs={'placeholder': 'Teléfono de contacto'}),
            'address': forms.TextInput(attrs={'placeholder': 'Dirección'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ciudad'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
        }


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'description', 'phone', 'address', 'city', 'logo', 'cover_image']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Nombre del negocio'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción breve del negocio…'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567', 'maxlength': '20'}),
            'address': forms.TextInput(attrs={'placeholder': 'Dirección física'}),
            'city': forms.TextInput(attrs={'placeholder': 'Ciudad'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('El nombre del negocio es obligatorio.')
        new_slug = slugify(name)
        if not new_slug:
            raise forms.ValidationError('El nombre no es válido.')
        qs = Business.objects.filter(slug=new_slug).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un negocio con ese nombre. Elige otro.')
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and not phone.isdigit():
            raise forms.ValidationError('El teléfono solo debe contener números.')
        if phone and len(phone) < 7:
            raise forms.ValidationError('El teléfono debe tener al menos 7 dígitos.')
        return phone

    def save(self, commit=True):
        biz = super().save(commit=False)
        biz.slug = slugify(biz.name)
        if commit:
            biz.save()
        return biz
