import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def document_upload_path(instance, filename):
    """Upload documents to media/documents/<username>/<filename>."""
    return f"documents/{instance.user.username}/{filename}"


class PrintOrder(models.Model):
    """A single print job submitted by a user."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('printed', 'Printed'),
    ]
    SIDE_CHOICES = [
        ('single', 'Single-Sided'),
        ('double', 'Double-Sided'),
    ]
    COLOR_CHOICES = [
        ('bw', 'Black & White'),
        ('color', 'Color'),
    ]
    LAYOUT_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='print_orders'
    )
    document = models.FileField(upload_to=document_upload_path, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # pdf, jpg, png
    file_size = models.PositiveIntegerField(default=0)  # bytes
    page_count = models.PositiveIntegerField(default=1)

    # Print options
    side_type = models.CharField(
        max_length=10, choices=SIDE_CHOICES, default='single'
    )
    color_type = models.CharField(
        max_length=10, choices=COLOR_CHOICES, default='bw'
    )
    layout = models.CharField(
        max_length=10, choices=LAYOUT_CHOICES, default='portrait'
    )
    copies = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True, default='')

    # Pricing & status
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )
    is_paid = models.BooleanField(default=False)
    file_deleted = models.BooleanField(default=False, help_text="True if file was deleted after 7 days")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} by {self.user.username} ({self.get_status_display()})"

    def mark_printing(self):
        """Mark order as currently being printed."""
        self.status = 'printing'
        self.save(update_fields=['status', 'updated_at'])

    def mark_printed(self):
        """Mark order as printed with timestamp."""
        self.status = 'printed'
        self.printed_at = timezone.now()
        self.save(update_fields=['status', 'printed_at', 'updated_at'])

    def mark_paid(self):
        """Toggle payment status."""
        self.is_paid = not self.is_paid
        self.save(update_fields=['is_paid', 'updated_at'])

    def cleanup_file(self):
        """Delete physical file from storage but keep database record."""
        if self.document and not self.file_deleted:
            try:
                if self.document.storage.exists(self.document.name):
                    self.document.storage.delete(self.document.name)
            except Exception:
                pass
            self.file_deleted = True
            self.document = None
            self.save(update_fields=['file_deleted', 'document', 'updated_at'])

    @classmethod
    def cleanup_expired_files(cls):
        """Auto cleanup files printed more than 7 days ago."""
        cutoff = timezone.now() - timezone.timedelta(days=7)
        expired_orders = cls.objects.filter(
            status='printed',
            file_deleted=False,
            printed_at__lte=cutoff
        )
        for order in expired_orders:
            order.cleanup_file()

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    @property
    def file_extension(self):
        """Get file extension from original filename."""
        _, ext = os.path.splitext(self.original_filename)
        return ext.lower()
