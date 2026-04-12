from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Business, DeliveryAddress


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['phone', 'full_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['phone', 'full_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Información personal', {'fields': ('full_name', 'avatar')}),
        ('Permisos', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'slug', 'is_active', 'is_suspended', 'created_at']
    list_filter = ['is_active', 'is_suspended']
    search_fields = ['name', 'owner__phone', 'slug']


@admin.register(DeliveryAddress)
class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'label', 'is_default']
