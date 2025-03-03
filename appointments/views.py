# appointments/views.py
import datetime
from datetime import timedelta
import pytz
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Slot, ConsultationScheduleConfig, RegistrationSetting
from .utils import get_slots_for_day
from django.http import JsonResponse, HttpResponse

def schedule(request):
    now = timezone.now()  # UTC
    moscow_tz = pytz.timezone("Europe/Moscow")
    now_moscow = now.astimezone(moscow_tz)
    today = now_moscow.date()

    # Определяем понедельник текущей недели (МСК) и следующий понедельник
    current_monday = today - timedelta(days=today.weekday())
    next_monday = current_monday + timedelta(days=7)

    # Получаем настройку открытия записи
    reg_setting = RegistrationSetting.objects.first()
    if reg_setting:
        # Вычисляем время открытия записи относительно текущей недели
        this_week_reg_open = moscow_tz.localize(
            datetime.datetime.combine(
                current_monday + timedelta(days=reg_setting.open_day),
                reg_setting.open_time
            )
        )
    else:
        # Значение по умолчанию: пятница 19:00
        this_week_reg_open = moscow_tz.localize(
            datetime.datetime.combine(current_monday + timedelta(days=4), datetime.time(19, 0))
        )

    # Если текущее время больше или равно времени открытия записи – запись на следующую неделю открыта
    registration_open_for_next_week = now_moscow >= this_week_reg_open
    registration_open_datetime = this_week_reg_open

    # Генерация расписания по секциям
    configs = ConsultationScheduleConfig.objects.all()
    past_consultations = {}      # консультации, дата которых < today
    current_consultations = {}   # консультации текущей недели, дата >= today
    next_week_consultations = {} # консультации следующей недели (если запись открыта)

    for config in configs:
        # Консультация в текущей неделе
        consultation_date_current = current_monday + timedelta(days=config.day_of_week)
        if consultation_date_current < today:
            slots = get_slots_for_day(consultation_date_current, config, None)
            past_consultations[consultation_date_current] = slots
        else:
            slots = get_slots_for_day(consultation_date_current, config, now_moscow)
            current_consultations[consultation_date_current] = slots

        # Консультация следующей недели
        consultation_date_next = next_monday + timedelta(days=config.day_of_week)
        if registration_open_for_next_week:
            slots = get_slots_for_day(consultation_date_next, config, None)
            next_week_consultations[consultation_date_next] = slots

    context = {
        'past_consultations': past_consultations,
        'current_consultations': current_consultations,
        'next_week_consultations': next_week_consultations,
        'registration_open_for_next_week': registration_open_for_next_week,
        'registration_open_datetime': registration_open_datetime,
        'now': now_moscow,
    }
    return render(request, 'appointments/schedule.html', context)

def book_slot(request, slot_id):
    slot = get_object_or_404(Slot, pk=slot_id)
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        if full_name and not slot.booked_by:
            slot.booked_by = full_name
            slot.save()
        return redirect('appointments:schedule')
    return render(request, 'appointments/book_slot.html', {'slot': slot})

def unbook_slot(request, slot_id):
    slot = get_object_or_404(Slot, pk=slot_id)
    if request.method == "POST":
        slot.booked_by = None
        slot.save()
    return redirect('appointments:schedule')


def book_nearest(request, consultation_date):
    """
    Находит ближайший свободный слот для указанной даты (YYYY-MM-DD) и записывает пользователя,
    если для этой даты еще нет записи с таким full_name.
    Ожидает POST-параметр full_name.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST allowed"}, status=405)

    full_name = request.POST.get("full_name", "").strip()
    if not full_name:
        return JsonResponse({"success": False, "error": "No full_name provided"}, status=400)

    try:
        cons_date = datetime.datetime.strptime(consultation_date, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "error": "Invalid date format"}, status=400)

    moscow_tz = pytz.timezone("Europe/Moscow")
    # Определяем границы дня в мск
    start_local = datetime.datetime.combine(cons_date, datetime.time.min)
    end_local = datetime.datetime.combine(cons_date, datetime.time.max)
    start_localized = moscow_tz.localize(start_local)
    end_localized = moscow_tz.localize(end_local)
    # Переводим границы в UTC
    start_utc = start_localized.astimezone(pytz.utc)
    end_utc = end_localized.astimezone(pytz.utc)

    # Проверяем, есть ли уже запись для этого full_name на заданную дату (без учета регистра)
    if Slot.objects.filter(
            start_time__gte=start_utc,
            start_time__lte=end_utc,
            booked_by__iexact=full_name
    ).exists():
        return JsonResponse({
            "success": False,
            "error": "Вы уже записаны на консультацию в этот день"
        }, status=400)

    now = timezone.now()
    # Если дата консультации — сегодня (в мск), отфильтруем слоты, которые уже начались
    if cons_date == now.astimezone(moscow_tz).date():
        free_slots = Slot.objects.filter(
            start_time__gte=start_utc,
            start_time__lte=end_utc,
            booked_by__isnull=True,
            start_time__gt=now
        )
    else:
        free_slots = Slot.objects.filter(
            start_time__gte=start_utc,
            start_time__lte=end_utc,
            booked_by__isnull=True
        )

    free_slot = free_slots.order_by('start_time').first()
    if free_slot:
        free_slot.booked_by = full_name
        free_slot.save()
        return JsonResponse({"success": True, "slot_id": free_slot.id})
    else:
        return JsonResponse({
            "success": False,
            "error": "Нет свободного слота в этот день"
        }, status=404)

def book_nearest_input(request, consultation_date):
    """
    Если у пользователя нет ФИО в localStorage, эта страница запрашивает ввод ФИО.
    При POST-запросе, если введено ФИО, происходит попытка записи на ближайший свободный слот для указанной даты.
    """
    try:
        cons_date = datetime.datetime.strptime(consultation_date, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponse("Неверный формат даты", status=400)

    error = None

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        if not full_name:
            error = "Пожалуйста, введите ФИО."
        else:
            moscow_tz = pytz.timezone("Europe/Moscow")
            start_local = datetime.datetime.combine(cons_date, datetime.time.min)
            end_local = datetime.datetime.combine(cons_date, datetime.time.max)
            start_localized = moscow_tz.localize(start_local)
            end_localized = moscow_tz.localize(end_local)
            start_utc = start_localized.astimezone(pytz.utc)
            end_utc = end_localized.astimezone(pytz.utc)
            now = timezone.now()
            if cons_date == now.astimezone(moscow_tz).date():
                free_slots = Slot.objects.filter(start_time__gte=start_utc, start_time__lte=end_utc, booked_by__isnull=True, start_time__gt=now)
            else:
                free_slots = Slot.objects.filter(start_time__gte=start_utc, start_time__lte=end_utc, booked_by__isnull=True)
            # Проверяем, если пользователь уже записан на этот день
            if Slot.objects.filter(start_time__gte=start_utc, start_time__lte=end_utc, booked_by__iexact=full_name).exists():
                error = "Вы уже записаны на консультацию в этот день."
            else:
                free_slot = free_slots.order_by('start_time').first()
                if free_slot:
                    free_slot.booked_by = full_name
                    free_slot.save()
                    # После успешной записи перенаправляем на страницу расписания
                    return redirect("appointments:schedule")
                else:
                    error = "Нет свободного слота в этот день."
    return render(request, "appointments/book_nearest_input.html", {
        "consultation_date": consultation_date,
        "error": error
    })