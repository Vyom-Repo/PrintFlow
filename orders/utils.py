"""Utility functions for document processing, page-range parsing, and pricing."""

import io
import os
from decimal import Decimal
from django.conf import settings
from pypdf import PdfReader, PdfWriter


# ---------------------------------------------------------------------------
# Page counting
# ---------------------------------------------------------------------------

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
            # Reset file position after reading so Django can still save it
            file_obj.seek(0)
            return max(page_count, 1)
        except Exception:
            # If PDF is corrupted or encrypted, default to 1
            file_obj.seek(0)
            return 1
    else:
        # Images are always treated as 1 page
        return 1


# ---------------------------------------------------------------------------
# Page-range parsing and validation
# ---------------------------------------------------------------------------

def parse_page_selection(selection_str, total_pages):
    """
    Parse and validate a user-supplied page-range string.

    Accepted formats
    ----------------
    * Single pages:  "1", "3", "7"
    * Ranges:        "5-19", "2-10"
    * Comma-mixed:   "1,3,5-10,15"

    Rules enforced
    --------------
    * All page numbers must be between 1 and total_pages (inclusive).
    * Range end must be >= range start (e.g. "10-5" is rejected).
    * Duplicate pages are silently removed.
    * Extra whitespace around tokens is ignored.

    Args:
        selection_str (str): Raw input from the user.
        total_pages (int): Total pages in the PDF.

    Returns:
        list[int]: Sorted, deduplicated list of 1-based page numbers.

    Raises:
        ValueError: With a human-readable message if validation fails.
    """
    selection_str = selection_str.strip()
    if not selection_str:
        raise ValueError("Page selection cannot be empty when 'Print Specific Pages' is chosen.")

    pages = set()
    tokens = selection_str.split(',')

    for raw_token in tokens:
        token = raw_token.strip()

        if not token:
            raise ValueError(
                f"Invalid page range: empty segment found near '{raw_token}'. "
                "Check for double commas or trailing commas."
            )

        if '-' in token:
            # Range token: e.g. "5-19"
            parts = token.split('-')
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise ValueError(
                    f"Invalid range '{token}'. Use the format 'start-end', e.g. '5-19'."
                )
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
            except ValueError:
                raise ValueError(
                    f"Non-numeric value in range '{token}'. Page numbers must be integers."
                )

            if start < 1:
                raise ValueError(
                    f"Page number {start} is invalid. Pages start at 1."
                )
            if end > total_pages:
                raise ValueError(
                    f"Page {end} exceeds the total number of pages in this PDF ({total_pages})."
                )
            if start > end:
                raise ValueError(
                    f"Invalid range '{token}': start page ({start}) must be ≤ end page ({end})."
                )

            pages.update(range(start, end + 1))

        else:
            # Single page token
            try:
                page_num = int(token)
            except ValueError:
                raise ValueError(
                    f"'{token}' is not a valid page number. Use integers only."
                )

            if page_num < 1:
                raise ValueError(
                    f"Page number {page_num} is invalid. Pages start at 1."
                )
            if page_num > total_pages:
                raise ValueError(
                    f"Page {page_num} exceeds the total number of pages in this PDF ({total_pages})."
                )

            pages.add(page_num)

    if not pages:
        raise ValueError("No valid pages found in the selection.")

    return sorted(pages)


# ---------------------------------------------------------------------------
# PDF extraction / slicing
# ---------------------------------------------------------------------------

def extract_pdf_pages(source_file_obj, page_numbers):
    """
    Create a new PDF containing only the specified pages.

    Args:
        source_file_obj: A file-like object (seek-able) of the source PDF.
        page_numbers (list[int]): Sorted list of 1-based page numbers to keep.

    Returns:
        bytes: The raw bytes of the new (trimmed) PDF.

    Raises:
        ValueError: If the source cannot be read as a PDF or a page index is
                    out of bounds.
    """
    try:
        source_file_obj.seek(0)
        reader = PdfReader(source_file_obj)
        total = len(reader.pages)
    except Exception as exc:
        raise ValueError(f"Could not read the uploaded PDF: {exc}") from exc

    writer = PdfWriter()

    for page_num in page_numbers:
        # page_numbers are 1-based; pypdf uses 0-based indexing
        idx = page_num - 1
        if idx < 0 or idx >= total:
            raise ValueError(
                f"Page {page_num} is out of bounds for this PDF ({total} pages)."
            )
        writer.add_page(reader.pages[idx])

    # Write the trimmed PDF to an in-memory buffer
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

def calculate_price(page_count, side_type, color_type, copies):
    """
    Calculate dynamic price based on print options.

    Pricing formula:
        - Single-sided: ₹0.50 per page
        - Double-sided: ₹0.33 per page (cheaper since both sides used)
        - Color multiplier: 3× the base price
        - Total = base_price × pages × copies

    NOTE: Pass `printable_page_count` (not `page_count`) when calling this
    function for new orders so that the user is only charged for selected pages.

    Args:
        page_count (int): Number of pages to price (should be printable_page_count).
        side_type (str): 'single' or 'double'
        color_type (str): 'bw' or 'color'
        copies (int): Number of copies

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


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

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
