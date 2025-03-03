# appointments/models.py
from django.db import models

class Slot(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    booked_by = models.CharField("ФИО студента", max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.start_time:%d.%m.%Y %H:%M} - {self.end_time:%H:%M}"

class ConsultationScheduleConfig(models.Model):
    DAY_CHOICES = (
       (0, "Понедельник"),
       (1, "Вторник"),
       (2, "Среда"),
       (3, "Четверг"),
       (4, "Пятница"),
       (5, "Суббота"),
       (6, "Воскресенье"),
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES, help_text="0 – понедельник, 6 – воскресенье")
    start_time = models.TimeField(help_text="Время начала консультации (МСК)")
    end_time = models.TimeField(help_text="Время окончания консультации (МСК)")
    slot_duration = models.PositiveIntegerField(help_text="Длительность слота в минутах")

    def __str__(self):
         return f"{self.get_day_of_week_display()}: {self.start_time} - {self.end_time} (слот: {self.slot_duration} мин)"

class RegistrationSetting(models.Model):
    DAY_CHOICES = (
       (0, "Понедельник"),
       (1, "Вторник"),
       (2, "Среда"),
       (3, "Четверг"),
       (4, "Пятница"),
       (5, "Суббота"),
       (6, "Воскресенье"),
    )
    open_day = models.IntegerField(choices=DAY_CHOICES, help_text="День недели, когда открывается запись на следующую неделю")
    open_time = models.TimeField(help_text="Время открытия записи в этот день (МСК)")

    def __str__(self):
         return f"Открытие записи: {self.get_open_day_display()} {self.open_time}"
