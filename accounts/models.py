from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for print management."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, default='')
    is_approved = models.BooleanField(default=False, help_text="Designates whether this user has been approved by admin.")

    class Meta:
        ordering = ['user__first_name', 'user__username']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def total_orders(self):
        return self.user.print_orders.count()

    @property
    def pending_orders(self):
        return self.user.print_orders.filter(status='pending').count()

    @property
    def total_spent(self):
        from django.db.models import Sum
        result = self.user.print_orders.aggregate(total=Sum('price'))
        val = result['total'] or 0
        return round(float(val), 2)

    @property
    def total_unpaid(self):
        from django.db.models import Sum
        result = self.user.print_orders.filter(is_paid=False).aggregate(total=Sum('price'))
        val = result['total'] or 0
        return round(float(val), 2)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
