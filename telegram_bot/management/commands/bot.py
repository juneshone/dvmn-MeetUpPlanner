import re
from django.core.management.base import BaseCommand
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from MeetUpPlanner import settings
from telegram.ext import Updater, CommandHandler, CallbackContext, \
    CallbackQueryHandler, MessageHandler, Filters
from telegram_bot.models import User


def start(update: Update, context: CallbackContext) -> None:
    full_name = update.message.from_user.full_name

    initial_message_text = (
        f"Привет, {full_name}. Я PyMeetBot — твой помощник на Мероприятия! 🎉\n"
        "Я помогу тебе задавать вопросы докладчикам, следить за программой и "
        "получать уведомления."
    )

    registration_keyboard = [
        [InlineKeyboardButton("Докладчик", callback_data='speaker')],
        [InlineKeyboardButton("Слушатель", callback_data='listener')]
    ]
    reply_markup = InlineKeyboardMarkup(registration_keyboard)

    update.message.reply_text(initial_message_text, reply_markup=reply_markup)


def choose_events(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith('speaker'):
        events_keyboard = [
            [InlineKeyboardButton(
                "Мероприятие 1", callback_data='event_speaker_1')],
            [InlineKeyboardButton(
                "Мероприятие 2", callback_data='event_speaker_2')]
        ]
        reply_markup = InlineKeyboardMarkup(events_keyboard)
        query.edit_message_text(
            'Получить программу мероприятий',
            reply_markup=reply_markup
        )

    if data.startswith('listener'):
        events_keyboard = [
            [InlineKeyboardButton(
                "Мероприятие 1", callback_data='event_listener_1')],
            [InlineKeyboardButton(
                "Мероприятие 2", callback_data='event_listener_2')]
        ]
        reply_markup = InlineKeyboardMarkup(events_keyboard)
        query.edit_message_text(
            'Выберите мероприятие',
            reply_markup=reply_markup
        )


def get_schedule_events(update: Update, context: CallbackContext):
    # autorize = False  # Future models
    query = update.callback_query
    query.answer()
    data = query.data
    if data.startswith('event_speaker'):
        events_keyboard = [
            [InlineKeyboardButton("Получить вопросы от пользователей",
                                  callback_data='#')]
        ]
        reply_markup = InlineKeyboardMarkup(events_keyboard)
        query.edit_message_text(
            'Программа мероприятия',
            reply_markup=reply_markup
        )
    # if data.startswith('event_listener'):
    #     if User.telegram_id != query.message.from_user.id:
    #         print(User.objects.get(username='user'), query.message.from_user.id)
    #         events_keyboard = [
    #             [InlineKeyboardButton("Регистрация",
    #                                   callback_data='register_user')]
    #         ]
    #         reply_markup = InlineKeyboardMarkup(events_keyboard)
    #         query.edit_message_text(
    #             'Вы не авторизованны',
    #             reply_markup=reply_markup
    #         )
    if data.startswith('event_listener'):
        try:
            user = User.objects.get(telegram_id=query.message.from_user.id)
        except User.DoesNotExist:
            user = None
            print(query.message.from_user.id)

        if user:
            events_keyboard = [
                [InlineKeyboardButton("Задать вопрос докладчику",
                                      callback_data='#')]
            ]
            reply_markup = InlineKeyboardMarkup(events_keyboard)
            query.edit_message_text(
                'Программа мероприятия',
                reply_markup=reply_markup
            )
        else:
            events_keyboard = [
                [InlineKeyboardButton("Регистрация", callback_data='register_user')]
            ]
            reply_markup = InlineKeyboardMarkup(events_keyboard)
            query.edit_message_text(
                'Вы не авторизованы',
                reply_markup=reply_markup)


def register_user(update: Update, context: CallbackContext):
    query = update.callback_query
    id = query.message.chat_id
    if query:
        query.answer()
        data = query.data
        if data.startswith('register_user'):
            context.user_data['step'] = 'FIO'
            query.message.reply_text('Введите ФИО')
            return

    message = update.message
    user_data = context.user_data

    if 'step' not in user_data:
        return

    if user_data['step'] == 'FIO':
        fio = message.text.strip()
        if not re.match(r'^[А-Яа-яЁёA-Za-z]+\s[А-Яа-яЁёA-Za-z]+\s[А-Яа-яЁёA-Za-z]+$', fio):
            message.reply_text(
                'Некорректный формат ФИО. Пожалуйста, введите Фамилия Имя Отчество.'
            )
            return
        user_data['fio'] = ' '.join(word.capitalize() for word in fio.split())
        user_data['step'] = 'PHONE'
        message.reply_text('Введите номер телефона')
        return

    if user_data['step'] == 'PHONE':
        phone = message.text
        if not re.match(r'^\+?\d{10,15}$', phone):
            message.reply_text(
                'Номер телефона некорректный. Пожалуйста, введите номер в формате +1234567890 или 1234567890.'
            )
            return
        user_data['phone'] = phone
        user_data['step'] = 'EMAIL'
        message.reply_text('Введите адрес электронной почты')
        return

    if user_data['step'] == 'EMAIL':
        email = message.text
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            message.reply_text(
                'Адрес электронной почты некорректный. Пожалуйста, введите правильный адрес.'
            )
            return
        user_data['email'] = email
        message.reply_text(
            f'Регистрация завершена. Ваши данные:\nФИО: {user_data["fio"]}\nТелефон: {user_data["phone"]}\nEmail: {user_data["email"]}'
        )
        new_member = User(
            username=user_data["fio"],
            telegram_id=id,
            email=user_data["email"],
            phonenumber=user_data["phone"]
            )
        new_member.save()
        user_data.clear()


class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(CallbackQueryHandler(
            choose_events,
            pattern='speaker')
        )
        dispatcher.add_handler(CallbackQueryHandler(
            choose_events,
            pattern='listener')
        )
        dispatcher.add_handler(CallbackQueryHandler(
            get_schedule_events,
            pattern='event_speaker')
        )
        dispatcher.add_handler(CallbackQueryHandler(
            get_schedule_events,
            pattern='event_listener')
        )
        dispatcher.add_handler(CallbackQueryHandler(
            register_user,
            pattern='register_user')
        )
        dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command, register_user)
        )

        updater.start_polling()
        updater.idle()
