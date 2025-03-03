# appointments/urls.py
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.schedule, name='schedule'),
    path('book/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('unbook/<int:slot_id>/', views.unbook_slot, name='unbook_slot'),
]
