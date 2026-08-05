import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def document_upload_path(instance, filename):
    """Upload original documents to media/documents/<username>/<filename>."""
    return f"documents/{instance.user.username}/{filename}"


def processed_upload_path(instance, filename):
    """Upload processed (trimmed) PDFs to media/documents/<username>/processed/<filename>."""
    return f"documents/{instance.user.username}/processed/{filename}"


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
    PRINT_MODE_CHOICES = [
        ('all', 'Print All Pages'),
        ('specific', 'Print Specific Pages'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='print_orders'
    )
    document = models.FileField(upload_to=document_upload_path, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # pdf, jpg, png
    file_size = models.PositiveIntegerField(default=0)  # bytes
    page_count = models.PositiveIntegerField(default=1)  # total pages in original file

    # -----------------------------------------------------------------------
    # Page-selection fields (added for selective-page printing feature)
    # All nullable/defaulted for full backward compatibility with existing rows
    # -----------------------------------------------------------------------

    # The trimmed PDF containing only the user-selected pages (null for images
    # or legacy orders where all pages are printed from the original document).
    processed_pdf = models.FileField(
        upload_to=processed_upload_path,
        null=True,
        blank=True,
        help_text="Auto-generated PDF containing only the selected pages."
    )

    # Whether the user chose to print all pages or a specific range.
    print_mode = models.CharField(
        max_length=10,
        choices=PRINT_MODE_CHOICES,
        default='all',
        help_text="'all' = every page; 'specific' = user-defined range."
    )

    # The raw page-range string entered by the user, e.g. "5-19" or "1,3,5-10".
    # Empty string means all pages.
    page_selection = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Page range string entered by the user, e.g. '5-19' or '1,3,5-10'."
    )

    # Number of pages that will actually be printed (used for pricing).
    # Equals page_count when print_mode='all'.
    printable_page_count = models.PositiveIntegerField(
        default=1,
        help_text="Pages actually printed; drives cost calculation."
    )

    # -----------------------------------------------------------------------

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
        """Delete physical files from storage but keep the database record."""
        if not self.file_deleted:
            # Delete original document
            if self.document:
                try:
                    if self.document.storage.exists(self.document.name):
                        self.document.storage.delete(self.document.name)
                except Exception:
                    pass
                self.document = None

            # Delete processed PDF (if it exists)
            if self.processed_pdf:
                try:
                    if self.processed_pdf.storage.exists(self.processed_pdf.name):
                        self.processed_pdf.storage.delete(self.processed_pdf.name)
                except Exception:
                    pass
                self.processed_pdf = None

            self.file_deleted = True
            self.save(update_fields=['file_deleted', 'document', 'processed_pdf', 'updated_at'])

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

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def print_file_url(self):
        """
        URL that the admin should open for printing.

        Returns the processed (trimmed) PDF URL when available, otherwise
        falls back to the original document URL. This ensures legacy orders
        (created before the page-selection feature) continue to work.
        """
        if self.processed_pdf:
            try:
                return self.processed_pdf.url
            except Exception:
                pass
        if self.document:
            try:
                return self.document.url
            except Exception:
                pass
        return None

    @property
    def printable_pages_display(self):
        """Human-readable printable pages label for admin/user views."""
        if self.print_mode == 'specific' and self.page_selection:
            return self.page_selection
        return f"All ({self.page_count})"

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
