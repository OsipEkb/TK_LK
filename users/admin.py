from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'external_id', 'is_active']
    search_fields = ['name', 'external_id']

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'organization', 'is_active']
    list_filter = ['user_type', 'organization', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'organization', 'external_id', 'phone', 'position')
        }),
    )