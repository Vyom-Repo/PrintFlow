from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'total_orders', 'total_spent']
    search_fields = ['user__username', 'user__first_name', 'phone']
