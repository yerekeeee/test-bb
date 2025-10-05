from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MasterProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'groups')

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('phone_number',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('phone_number', 'first_name', 'last_name')}),
    )


@admin.register(MasterProfile)
class MasterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'average_rating', 'review_count')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    filter_horizontal = ('services',)