import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PrintOrder
from .forms import PrintOrderForm
from .utils import count_pages, calculate_price, validate_file_extension, get_file_type_label


@login_required
def upload_document(request):
    """Handle document upload with auto page counting and pricing."""
    if request.method == 'POST':
        form = PrintOrderForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['document']

            # Validate file extension
            is_valid, extension = validate_file_extension(uploaded_file.name)
            if not is_valid:
                messages.error(request, f'File type "{extension}" is not supported. Please upload PDF, JPG, or PNG files.')
                return render(request, 'orders/upload.html', {'form': form})

            # Create order but don't save to DB yet
            order = form.save(commit=False)
            order.user = request.user
            order.original_filename = uploaded_file.name
            order.file_type = get_file_type_label(extension)
            order.file_size = uploaded_file.size

            # Count pages from the uploaded file
            order.page_count = count_pages(uploaded_file, extension)

            # Calculate dynamic price
            order.price = calculate_price(
                order.page_count,
                order.side_type,
                order.color_type,
                order.copies
            )

            order.save()
            messages.success(
                request,
                f'📄 "{order.original_filename}" uploaded successfully! '
                f'{order.page_count} page(s) detected — Price: ₹{order.price}'
            )
            return redirect('orders:my_orders')
    else:
        form = PrintOrderForm()

    return render(request, 'orders/upload.html', {'form': form})


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
