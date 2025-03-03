# appointments/utils.py
import datetime
from datetime import timedelta
import pytz
from .models import Slot

def get_slots_for_day(date, config, now_moscow=None):
    """
    Генерирует список слотов для заданного дня (date – объект date) на основе настроек config.
    Если now_moscow передан (для дней текущей недели), то слоты, время которых уже началось, пропускаются.
    """
    slots = []
    moscow_tz = pytz.timezone("Europe/Moscow")
    start_dt = moscow_tz.localize(datetime.datetime.combine(date, config.start_time))
    end_dt = moscow_tz.localize(datetime.datetime.combine(date, config.end_time))
    current = start_dt
    while current < end_dt:
        slot_end = current + timedelta(minutes=config.slot_duration)
        # Если генерируем для текущего дня и время уже прошло, пропускаем этот слот
        if now_moscow and date == now_moscow.date() and current < now_moscow:
            current = slot_end
            continue
        start_utc = current.astimezone(pytz.utc)
        end_utc = slot_end.astimezone(pytz.utc)
        slot_obj, created = Slot.objects.get_or_create(
            start_time=start_utc,
            end_time=end_utc,
            defaults={'booked_by': None}
        )
        slots.append(slot_obj)
        current = slot_end
    return slots
