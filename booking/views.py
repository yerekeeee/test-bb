from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import F, ExpressionWrapper, fields, Count, Sum, Q
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .models import Service, Appointment, Review
from .forms import ReviewForm
from users.models import MasterProfile
import datetime
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncMonth
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date

def service_selection(request):
    services = Service.objects.all()
    return render(request, 'booking/1_service_selection.html', {'services': services})


def master_selection(request):
    service_ids = request.GET.getlist('services')
    if not service_ids:
        return redirect('booking:service_selection')

    services = Service.objects.filter(id__in=service_ids)
    masters = MasterProfile.objects.filter(services__in=services).distinct()

    context = {
        'masters': masters,
        'selected_services_json': service_ids
    }
    return render(request, 'booking/2_master_selection.html', context)


def calendar_view(request, master_id):
    master = get_object_or_404(MasterProfile, id=master_id)
    service_ids = request.GET.getlist('services')

    total_duration = Service.objects.filter(id__in=service_ids).aggregate(
        total=Sum('duration')
    )['total'] or timedelta()

    context = {
        'master': master,
        'selected_services_json': service_ids,
        'total_duration_minutes': int(total_duration.total_seconds() / 60)
    }
    return render(request, 'booking/3_calendar_view.html', context)


def get_available_slots(request, master_id):
    date_str = request.GET.get('date')
    total_duration_minutes = int(request.GET.get('duration', 0))
    total_duration = timedelta(minutes=total_duration_minutes)

    target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    work_start, work_end, slot_interval = 10, 22, 30

    appointments = Appointment.objects.filter(master_id=master_id, start_time__date=target_date)

    available_slots = []

    # ▼▼▼ НАЧАЛО ИЗМЕНЕНИЙ ▼▼▼

    # 1. Получаем текущее точное время
    now = timezone.now()
    today = now.date()

    # Устанавливаем начальное время для цикла
    current_time = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(work_start, 0)))
    end_of_work = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(work_end, 0)))

    while current_time + total_duration <= end_of_work:
        # 2. Новая проверка: если день сегодня И время слота уже прошло, пропускаем его
        if target_date == today and current_time < now:
            # Переходим к следующему слоту, не добавляя текущий
            current_time += timedelta(minutes=slot_interval)
            continue

        # Проверка на конфликт с другими записями (остается без изменений)
        is_free = not appointments.filter(start_time__lt=current_time + total_duration,
                                          end_time__gt=current_time).exists()

        if is_free:
            available_slots.append(current_time.strftime('%H:%M'))

        current_time += timedelta(minutes=slot_interval)

    # ▲▲▲ КОНЕЦ ИЗМЕНЕНИЙ ▲▲▲

    return JsonResponse({'available_slots': available_slots})


def get_confirmation_details(request):
    master_id = request.GET.get('master_id')
    service_ids = request.GET.getlist('services[]')
    time_str = request.GET.get('time')
    date_str = request.GET.get('date')

    master = get_object_or_404(MasterProfile, id=master_id)
    services = Service.objects.filter(id__in=service_ids)

    total_price = sum(s.price for s in services)

    data = {
        'master_name': master.user.get_full_name(),
        'date': date_str, 'time': time_str,
        'services': [{'name': s.name, 'price': f"{s.price:g}"} for s in services],
        'total_price': f"{total_price:g}"
    }
    return JsonResponse(data)


def create_appointment(request):
    if request.method == 'POST':
        master_id = request.POST.get('master_id')
        service_ids = request.POST.getlist('services[]')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        master = get_object_or_404(MasterProfile, id=master_id)
        services = Service.objects.filter(id__in=service_ids)

        total_duration = sum([s.duration for s in services], timedelta())
        total_price = sum([s.price for s in services])

        start_time = timezone.make_aware(datetime.datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M'))
        end_time = start_time + total_duration

        appointment = Appointment.objects.create(
            client=request.user, master=master, start_time=start_time, end_time=end_time,
            total_price=total_price, total_duration=total_duration
        )
        appointment.services.set(services)

        success_url = reverse('booking:booking_success', kwargs={'appointment_id': appointment.id})

        return JsonResponse({'status': 'success', 'redirect_url': success_url})

    return JsonResponse({'status': 'error'}, status=400)


def booking_success(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)
    return render(request, 'booking/success.html', {'appointment': appointment})


@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()
    one_week_ago = today - timedelta(days=6)
    one_year_ago = today - timedelta(days=365)

    # --- Данные для KPI-карточек ---
    appointments_today = Appointment.objects.filter(start_time__date=today)
    new_appointments_count = appointments_today.count()
    revenue_today = appointments_today.aggregate(total=Sum('total_price'))['total'] or 0
    master_load = MasterProfile.objects.annotate(
        appointment_count=Count('appointments', filter=Q(appointments__start_time__date=today))
    ).select_related('user').order_by('-appointment_count')

    # --- Данные для графика динамики записей ---
    appointments_per_day = Appointment.objects.filter(start_time__date__gte=one_week_ago) \
        .annotate(day=TruncDate('start_time')).values('day') \
        .annotate(count=Count('id')).order_by('day')
    chart_labels = [(one_week_ago + timedelta(days=i)).strftime("%d %b") for i in range(7)]
    chart_data = [0] * 7
    day_map = {label: i for i, label in enumerate(chart_labels)}
    for entry in appointments_per_day:
        label = entry['day'].strftime("%d %b")
        if label in day_map:
            chart_data[day_map[label]] = entry['count']

    # --- Данные для графика динамики выручки по месяцам (НОВЫЙ БЛОК) ---
    revenue_by_month = Appointment.objects.filter(start_time__gte=one_year_ago) \
        .annotate(month=TruncMonth('start_time')) \
        .values('month') \
        .annotate(total_revenue=Sum('total_price')) \
        .order_by('month')

    revenue_chart_labels = [r['month'].strftime("%b %Y") for r in revenue_by_month]
    revenue_chart_data = [float(r['total_revenue']) for r in revenue_by_month]

    # --- Последние отзывы ---
    latest_reviews = Review.objects.select_related('client', 'master__user').order_by('-created_at')[:5]

    context = {
        'new_appointments_count': new_appointments_count,
        'revenue_today': revenue_today,
        'master_load': master_load,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'latest_reviews': latest_reviews,
        'revenue_chart_labels': revenue_chart_labels,  # <-- Новые данные
        'revenue_chart_data': revenue_chart_data,  # <-- Новые данные
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@staff_member_required
def all_appointments_view(request):
    appointments_list = Appointment.objects.select_related('client', 'master__user').order_by('-start_time')
    masters = MasterProfile.objects.all()

    # Фильтрация
    master_id = request.GET.get('master')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if master_id:
        appointments_list = appointments_list.filter(master__id=master_id)
    if start_date and end_date:
        appointments_list = appointments_list.filter(start_time__range=[start_date, end_date])

    # Пагинация
    paginator = Paginator(appointments_list, 15)  # По 15 записей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'masters': masters,
        'selected_master': int(master_id) if master_id else None,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'dashboard/all_appointments.html', context)


@login_required
def add_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)

    # Проверяем, что запись уже прошла и на нее еще нет отзыва
    if appointment.start_time >= timezone.now():
        # тут можно вернуть страницу с ошибкой
        return redirect('users:profile')
    if hasattr(appointment, 'review'):
        # отзыв уже есть
        return redirect('users:profile')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.master = appointment.master
            review.client = request.user
            review.save()
            return redirect('users:profile')
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'appointment': appointment
    }
    return render(request, 'booking/add_review.html', context)


def master_reviews(request, master_id):
    master = get_object_or_404(MasterProfile, id=master_id)
    reviews = master.reviews.order_by('-created_at')

    context = {
        'master': master,
        'reviews': reviews
    }
    return render(request, 'booking/master_reviews.html', context)


# @staff_member_required
# def schedule_view(request):
#     masters = MasterProfile.objects.all().order_by('user__first_name')
#     selected_master_id = request.GET.get('master')
#
#     appointments_list = Appointment.objects.all()
#     selected_master = None
#
#     # Фильтруем по мастеру, если он выбран
#     if selected_master_id:
#         selected_master = get_object_or_404(MasterProfile, id=selected_master_id)
#         appointments_list = appointments_list.filter(master=selected_master)
#
#     date_str = request.GET.get('date')
#     selected_date = parse_date(date_str) if date_str else timezone.localdate()
#
#     # Фильтруем по дате
#     appointments_on_date = appointments_list.filter(start_time__date=selected_date)\
#         .select_related('client', 'master__user').prefetch_related('services').order_by('start_time')
#
#     # Разделяем записи на Утро, День, Вечер
#     morning_appointments = [app for app in appointments_on_date if 9 <= timezone.localtime(app.start_time).hour < 12]
#     day_appointments = [app for app in appointments_on_date if 12 <= timezone.localtime(app.start_time).hour < 18]
#     evening_appointments = [app for app in appointments_on_date if 18 <= timezone.localtime(app.start_time).hour < 23]
#
#     context = {
#         'masters': masters,
#         'selected_master': selected_master,
#         'selected_date': selected_date,
#         'morning_appointments': morning_appointments,
#         'day_appointments': day_appointments,
#         'evening_appointments': evening_appointments,
#     }
#     return render(request, 'dashboard/schedule_view.html', context)

@staff_member_required
def schedule_view(request):
    masters = MasterProfile.objects.all().order_by('user__first_name')
    selected_master_id = request.GET.get('master')

    appointments_list = Appointment.objects.all()
    selected_master = None

    if selected_master_id:
        selected_master = get_object_or_404(MasterProfile, id=selected_master_id)
        appointments_list = appointments_list.filter(master=selected_master)

    date_str = request.GET.get('date')
    selected_date = parse_date(date_str) if date_str else timezone.localdate()

    appointments_on_date = appointments_list.filter(start_time__date=selected_date) \
        .select_related('client', 'master__user').prefetch_related('services').order_by('start_time')

    # Функция для обработки и добавления данных к каждой записи
    def process_appointment(app):
        services_list = app.services.all()
        # ▼▼▼ ГОТОВИМ СТРОКУ ДЛЯ WHATSAPP ЗДЕСЬ ▼▼▼
        app.services_text_for_whatsapp = "\n".join(
            [f"- {s.name} ({int(s.price)} тг.)" for s in services_list]
        )
        return app

    # Разделяем записи на Утро, День, Вечер, применяя обработку
    morning_appointments = [process_appointment(app) for app in appointments_on_date if
                            9 <= timezone.localtime(app.start_time).hour < 12]
    day_appointments = [process_appointment(app) for app in appointments_on_date if
                        12 <= timezone.localtime(app.start_time).hour < 18]
    evening_appointments = [process_appointment(app) for app in appointments_on_date if
                            18 <= timezone.localtime(app.start_time).hour < 23]

    context = {
        'masters': masters,
        'selected_master': selected_master,
        'selected_date': selected_date,
        'morning_appointments': morning_appointments,
        'day_appointments': day_appointments,
        'evening_appointments': evening_appointments,
    }
    return render(request, 'dashboard/schedule_view.html', context)