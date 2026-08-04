from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm


def signup_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('orders:my_orders')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            # If user is staff/superuser, auto-approve
            if user.is_staff or user.is_superuser:
                user.profile.is_approved = True
                user.profile.save()
                login(request, user)
                messages.success(request, f'Welcome to PrintFlow, {user.first_name}! 🎉')
                return redirect('orders:my_orders')
            else:
                user.profile.is_approved = False
                user.profile.save()
                messages.info(request, f'Account created for {user.first_name or user.username}! ⌛ Your account is pending admin approval before you can log in.')
                return redirect('accounts:login')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """Handle user login with admin approval check."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard:admin_dashboard')
        return redirect('orders:my_orders')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check approval status for non-staff users
            if not user.is_staff and not getattr(user.profile, 'is_approved', False):
                messages.error(request, '⌛ Your account is pending admin approval. Please ask the admin to approve your account.')
                return render(request, 'accounts/login.html')

            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            if user.is_staff:
                return redirect('dashboard:admin_dashboard')
            return redirect('orders:my_orders')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Display user profile with order summary."""
    user = request.user
    orders = user.print_orders.all().order_by('-created_at')[:5]
    context = {
        'profile': user.profile,
        'recent_orders': orders,
    }
    return render(request, 'accounts/profile.html', context)
