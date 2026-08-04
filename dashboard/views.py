from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from orders.models import PrintOrder


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with sidebar users and order queue."""
    # All registered users (non-staff)
    users = User.objects.filter(is_staff=False).select_related('profile').annotate(
        order_count=Count('print_orders'),
        pending_count=Count('print_orders', filter=Q(print_orders__status='pending')),
        total_spent=Sum('print_orders__price'),
    ).order_by('first_name', 'username')

    # Pending and printing orders (the queue)
    active_orders = PrintOrder.objects.filter(
        status__in=['pending', 'printing']
    ).select_related('user').order_by('-created_at')

    # Today's stats
    today = timezone.now().date()
    today_orders = PrintOrder.objects.filter(created_at__date=today)
    stats = {
        'total_pending': PrintOrder.objects.filter(status='pending').count(),
        'total_printing': PrintOrder.objects.filter(status='printing').count(),
        'today_orders': today_orders.count(),
        'today_revenue': today_orders.aggregate(total=Sum('price'))['total'] or 0,
        'total_unpaid': PrintOrder.objects.filter(is_paid=False).aggregate(
            total=Sum('price')
        )['total'] or 0,
        'total_users': User.objects.filter(is_staff=False).count(),
    }

    context = {
        'users': users,
        'active_orders': active_orders,
        'stats': stats,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@staff_member_required
def mark_printing(request, order_id):
    """Mark an order as currently printing."""
    order = get_object_or_404(PrintOrder, id=order_id)
    order.mark_printing()
    messages.info(request, f'🖨️ "{order.original_filename}" marked as printing.')
    return redirect('dashboard:admin_dashboard')


@staff_member_required
def mark_printed(request, order_id):
    """Mark an order as printed."""
    order = get_object_or_404(PrintOrder, id=order_id)
    order.mark_printed()
    messages.success(request, f'✅ "{order.original_filename}" marked as printed!')
    return redirect('dashboard:admin_dashboard')


@staff_member_required
def mark_paid(request, order_id):
    """Toggle payment status for an order."""
    order = get_object_or_404(PrintOrder, id=order_id)
    order.mark_paid()
    status = "paid" if order.is_paid else "unpaid"
    messages.success(request, f'💰 "{order.original_filename}" marked as {status}.')
    return redirect('dashboard:admin_dashboard')


@staff_member_required
def user_detail(request, user_id):
    """View a specific user's order history."""
    target_user = get_object_or_404(User, id=user_id, is_staff=False)
    orders = PrintOrder.objects.filter(user=target_user).order_by('-created_at')

    total_spent = orders.aggregate(total=Sum('price'))['total'] or 0
    total_unpaid = orders.filter(is_paid=False).aggregate(total=Sum('price'))['total'] or 0

    context = {
        'target_user': target_user,
        'orders': orders,
        'total_spent': total_spent,
        'total_unpaid': total_unpaid,
    }
    return render(request, 'dashboard/user_detail.html', context)


@staff_member_required
def all_orders(request):
    """View all orders (including printed) with filters."""
    status_filter = request.GET.get('status', 'all')

    orders = PrintOrder.objects.all().select_related('user').order_by('-created_at')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/all_orders.html', context)


@staff_member_required
def mark_all_paid(request, user_id):
    """Mark all unpaid orders for a user as paid."""
    target_user = get_object_or_404(User, id=user_id, is_staff=False)
    unpaid_orders = PrintOrder.objects.filter(user=target_user, is_paid=False)
    count = unpaid_orders.update(is_paid=True)
    messages.success(request, f'✅ Marked {count} orders as paid for {target_user.get_full_name() or target_user.username}.')
    return redirect('dashboard:user_detail', user_id=user_id)


@staff_member_required
def approve_user(request, user_id):
    """Approve a user account."""
    target_user = get_object_or_404(User, id=user_id, is_staff=False)
    target_user.profile.is_approved = True
    target_user.profile.save()
    messages.success(request, f'✅ User {target_user.get_full_name() or target_user.username} approved.')
    return redirect('dashboard:admin_dashboard')
