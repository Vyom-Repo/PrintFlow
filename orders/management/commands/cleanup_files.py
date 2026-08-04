import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import PrintOrder

class Command(BaseCommand):
    help = 'Cleans up document files for printed orders older than 7 days.'

    def handle(self, *args, **kwargs):
        seven_days_ago = timezone.now() - timedelta(days=7)
        # Find orders that are printed and created > 7 days ago
        orders = PrintOrder.objects.filter(status='printed', created_at__lt=seven_days_ago)
        
        count = 0
        for order in orders:
            if order.document and os.path.isfile(order.document.path):
                try:
                    os.remove(order.document.path)
                    # We don't remove the order from DB, just the file
                    order.document = None
                    order.save(update_fields=['document'])
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error deleting file for order {order.id}: {e}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {count} files."))
