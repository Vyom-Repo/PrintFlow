from django.contrib import admin
from .models import PrintOrder


@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'user',
        'page_count', 'print_mode', 'page_selection', 'printable_page_count',
        'side_type', 'color_type', 'price', 'status', 'is_paid', 'created_at',
    ]
    list_filter = ['status', 'is_paid', 'side_type', 'color_type', 'print_mode', 'created_at']
    search_fields = ['original_filename', 'user__username', 'user__first_name', 'page_selection']
    readonly_fields = [
        'page_count', 'printable_page_count', 'price', 'file_size',
        'print_mode', 'page_selection',
        'created_at', 'updated_at', 'printed_at',
    ]
