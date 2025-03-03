# appointments/urls.py
from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.schedule, name='schedule'),
    path('book/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('unbook/<int:slot_id>/', views.unbook_slot, name='unbook_slot'),
    path('book_nearest/<str:consultation_date>/', views.book_nearest, name='book_nearest'),
    path('book_nearest_input/<str:consultation_date>/', views.book_nearest_input, name='book_nearest_input'),
]
