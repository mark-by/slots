# appointments/views.py
import datetime
from datetime import timedelta
import pytz
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Slot, ConsultationScheduleConfig, RegistrationSetting
from .utils import get_slots_for_day

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
