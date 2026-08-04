"""Utility functions for document processing and pricing."""

import os
from decimal import Decimal
from django.conf import settings
from pypdf import PdfReader


def count_pages(file_obj, file_extension):
    """
    Count the number of pages in an uploaded document.

    Args:
        file_obj: Django UploadedFile object
        file_extension: File extension (e.g., '.pdf', '.jpg')

    Returns:
        int: Number of pages (1 for images, actual count for PDFs)
    """
    if file_extension == '.pdf':
        try:
            reader = PdfReader(file_obj)
            page_count = len(reader.pages)
            # Reset file position after reading
            file_obj.seek(0)
            return max(page_count, 1)
        except Exception:
            # If PDF is corrupted or encrypted, default to 1
            file_obj.seek(0)
            return 1
    else:
        # Images are always 1 page
        return 1


def calculate_price(page_count, side_type, color_type, copies):
    """
    Calculate dynamic price based on print options.

    Pricing formula:
        - Single-sided: ₹0.50 per page
        - Double-sided: ₹0.33 per page (cheaper since both sides used)
        - Color multiplier: 3x the base price
        - Total = base_price × pages × copies

    Args:
        page_count: Number of pages in the document
        side_type: 'single' or 'double'
        color_type: 'bw' or 'color'
        copies: Number of copies

    Returns:
        Decimal: Total price in INR
    """
    if side_type == 'single':
        base_rate = Decimal(str(settings.PRICE_SINGLE_SIDED))
    else:
        base_rate = Decimal(str(settings.PRICE_DOUBLE_SIDED))

    if color_type == 'color':
        base_rate *= Decimal(str(settings.PRICE_COLOR_MULTIPLIER))

    total = base_rate * Decimal(str(page_count)) * Decimal(str(copies))
    return total.quantize(Decimal('0.01'))


def validate_file_extension(filename):
    """
    Check if the uploaded file has an allowed extension.

    Returns:
        tuple: (is_valid: bool, extension: str)
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    allowed = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.pdf', '.jpg', '.jpeg', '.png'])
    return ext in allowed, ext


def get_file_type_label(extension):
    """Get a human-readable label for the file type."""
    labels = {
        '.pdf': 'PDF',
        '.jpg': 'Image',
        '.jpeg': 'Image',
        '.png': 'Image',
    }
    return labels.get(extension, 'Unknown')
