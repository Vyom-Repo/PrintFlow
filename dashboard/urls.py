from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('orders/', views.all_orders, name='all_orders'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('order/<int:order_id>/printing/', views.mark_printing, name='mark_printing'),
    path('order/<int:order_id>/printed/', views.mark_printed, name='mark_printed'),
    path('order/<int:order_id>/paid/', views.mark_paid, name='mark_paid'),
    path('user/<int:user_id>/mark_all_paid/', views.mark_all_paid, name='mark_all_paid'),
    path('user/<int:user_id>/approve/', views.approve_user, name='approve_user'),
]
