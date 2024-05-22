from django.contrib import admin

from telegram_bot.models import User, Event, Question


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('telegram_id', 'phonenumber', 'username',)
    list_display = ('role', 'telegram_id', 'username', 'phonenumber',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'speaker', 'start_time',)
    raw_id_fields = ('speaker',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ('description',)
    list_display = ('description', 'listener', 'speaker', 'status',)
