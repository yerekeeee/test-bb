from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('select-service/', views.service_selection, name='service_selection'),
    path('select-master/', views.master_selection, name='master_selection'),
    path('calendar/<int:master_id>/', views.calendar_view, name='calendar'),
    path('success/<int:appointment_id>/', views.booking_success, name='booking_success'),

    path('api/slots/<int:master_id>/', views.get_available_slots, name='get_slots'),
    path('api/confirmation-details/', views.get_confirmation_details, name='get_confirmation_details'),
    path('api/create-appointment/', views.create_appointment, name='create_appointment'),
    path('all-appointments/', views.all_appointments_view, name='all_appointments'),
    path('schedule/', views.schedule_view, name='schedule_view'),  # <--- Вот ваш URL
    path('review/add/<int:appointment_id>/', views.add_review, name='add_review'),
    path('master/<int:master_id>/reviews/', views.master_reviews, name='master_reviews'),

]