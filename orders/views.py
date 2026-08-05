import os
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import PrintOrder
from .forms import PrintOrderForm
from .utils import (
    count_pages,
    calculate_price,
    validate_file_extension,
    get_file_type_label,
    parse_page_selection,
    extract_pdf_pages,
)


@login_required
def upload_document(request):
    """
    Handle document upload with page selection, PDF slicing, and pricing.

    Workflow
    --------
    1. Validate file extension.
    2. Count total pages in the uploaded PDF.
    3. Read print_mode ('all' or 'specific') from the form.
    4. If 'specific':
       a. Parse and validate page_selection against total pages.
       b. Extract the requested pages into a new in-memory PDF.
       c. Attach the trimmed PDF to order.processed_pdf.
       d. Set printable_page_count = len(selected_pages).
    5. If 'all':
       a. printable_page_count = total page count.
    6. Calculate price using printable_page_count.
    7. Save the order (Django saves both FileFields to storage).
    """
    if request.method == 'POST':
        form = PrintOrderForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES.get('document')

            if not uploaded_file:
                messages.error(request, 'Please upload a document.')
                return render(request, 'orders/upload.html', {'form': form})

            # Validate file extension
            is_valid, extension = validate_file_extension(uploaded_file.name)
            if not is_valid:
                messages.error(
                    request,
                    f'File type "{extension}" is not supported. '
                    'Please upload PDF, JPG, or PNG files.'
                )
                return render(request, 'orders/upload.html', {'form': form})

            # Build the order object (not yet saved to DB)
            order = form.save(commit=False)
            order.user = request.user
            order.original_filename = uploaded_file.name
            order.file_type = get_file_type_label(extension)
            order.file_size = uploaded_file.size

            # Count total pages in the original file
            total_pages = count_pages(uploaded_file, extension)
            order.page_count = total_pages

            # Read page-selection choices from the validated form data
            print_mode = form.cleaned_data.get('print_mode', 'all')
            page_selection_str = form.cleaned_data.get('page_selection', '').strip()

            order.print_mode = print_mode

            if print_mode == 'specific' and extension == '.pdf':
                # ----------------------------------------------------------
                # Specific page range: parse, validate, slice, and store
                # ----------------------------------------------------------
                try:
                    page_numbers = parse_page_selection(page_selection_str, total_pages)
                except ValueError as exc:
                    messages.error(request, f'Page selection error: {exc}')
                    return render(request, 'orders/upload.html', {'form': form})

                # Extract the selected pages into a new in-memory PDF
                try:
                    trimmed_bytes = extract_pdf_pages(uploaded_file, page_numbers)
                except ValueError as exc:
                    messages.error(request, f'Could not process PDF: {exc}')
                    return render(request, 'orders/upload.html', {'form': form})

                # Wrap bytes in an InMemoryUploadedFile so Django's storage
                # backend can save it just like any other uploaded file
                base_name, _ = os.path.splitext(uploaded_file.name)
                processed_filename = f"{base_name}_processed.pdf"
                trimmed_file = InMemoryUploadedFile(
                    file=io.BytesIO(trimmed_bytes),
                    field_name='processed_pdf',
                    name=processed_filename,
                    content_type='application/pdf',
                    size=len(trimmed_bytes),
                    charset=None,
                )
                order.processed_pdf = trimmed_file
                order.page_selection = page_selection_str
                order.printable_page_count = len(page_numbers)

            else:
                # ----------------------------------------------------------
                # All pages (or non-PDF file): no slicing needed
                # ----------------------------------------------------------
                order.print_mode = 'all'
                order.page_selection = ''
                order.printable_page_count = total_pages

            # Calculate price using only the printable pages
            order.price = calculate_price(
                order.printable_page_count,
                order.side_type,
                order.color_type,
                order.copies,
            )

            order.save()

            # Build a helpful success message
            if order.print_mode == 'specific':
                page_info = (
                    f'{order.printable_page_count} of {order.page_count} pages '
                    f'(pages: {order.page_selection})'
                )
            else:
                page_info = f'{order.page_count} page(s)'

            messages.success(
                request,
                f'📄 "{order.original_filename}" uploaded successfully! '
                f'{page_info} — Price: ₹{order.price}'
            )
            return redirect('orders:my_orders')

    else:
        form = PrintOrderForm()

    return render(request, 'orders/upload.html', {'form': form})


@login_required
def get_page_count(request):
    """
    AJAX endpoint: accept a PDF upload and return its page count.

    Used by the upload form's JavaScript to display the total pages
    immediately after the user selects a file, enabling the live
    page-count and price preview without a full form submit.

    Method: POST
    Body:   multipart/form-data with 'document' file field
    Returns: JSON {"total_pages": N} or {"error": "..."}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    uploaded_file = request.FILES.get('document')
    if not uploaded_file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()

    if ext == '.pdf':
        total_pages = count_pages(uploaded_file, ext)
    else:
        # Images are always 1 page
        total_pages = 1

    return JsonResponse({'total_pages': total_pages})


@login_required
def my_orders(request):
    """List all orders for the logged-in user."""
    orders = PrintOrder.objects.filter(user=request.user).order_by('-created_at')

    # Stats for the user
    total_orders = orders.count()
    pending_count = orders.filter(status='pending').count()
    printed_count = orders.filter(status='printed').count()

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'printed_count': printed_count,
    }
    return render(request, 'orders/my_orders.html', context)


@login_required
def order_detail(request, order_id):
    """View details of a single order."""
    order = get_object_or_404(PrintOrder, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
