from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.my_orders, name='my_orders'),
    path('upload/', views.upload_document, name='upload'),
    path('get-page-count/', views.get_page_count, name='get_page_count'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
]
