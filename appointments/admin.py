# appointments/admin.py
from django.contrib import admin
from .models import Slot, ConsultationScheduleConfig, RegistrationSetting

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'booked_by')
    list_filter = ('start_time',)
    search_fields = ('booked_by',)

@admin.register(ConsultationScheduleConfig)
class ConsultationScheduleConfigAdmin(admin.ModelAdmin):
    list_display = ('get_day_of_week_display', 'start_time', 'end_time', 'slot_duration')
    list_filter = ('day_of_week',)

@admin.register(RegistrationSetting)
class RegistrationSettingAdmin(admin.ModelAdmin):
    list_display = ('get_open_day_display', 'open_time')
