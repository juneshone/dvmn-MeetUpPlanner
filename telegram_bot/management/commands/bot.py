import re
import random
from django.core.management.base import BaseCommand

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http.response import Http404
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from MeetUpPlanner import settings
from telegram.ext import Updater, CommandHandler, CallbackContext, \
    CallbackQueryHandler, MessageHandler, Filters
from telegram_bot.models import User, Event, Question
from textwrap import dedent


def start(update: Update, context: CallbackContext) -> None:
    full_name = update.message.from_user.full_name

    initial_message_text = (
        f"Привет, {full_name}. Я PyMeetBot — твой помощник на Мероприятиях! 🎉\n"
        "Я помогу тебе задавать вопросы докладчикам, следить за программой и "
        "получать уведомления."
    )
    registration_keyboard = [
        [InlineKeyboardButton("Продолжить", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(registration_keyboard)

    update.message.reply_text(initial_message_text, reply_markup=reply_markup)


def choose_events(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    events = Event.objects.filter(end_time__gte=timezone.now())
    if events:
        events_keyboard = [
            [InlineKeyboardButton(
                f"{event.title}",
                callback_data=str(event.id)
                )
            ] for event in events
        ]
        reply_markup = InlineKeyboardMarkup(events_keyboard)
        query.edit_message_text(
            'Выберите мероприятие',
            reply_markup=reply_markup
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Актуальных мероприятий нет',
        )


def get_schedule_events(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data
    event_id = int(data)
    event = Event.objects.get(id=event_id)
    context.bot_data['event'] = event.id
    text = dedent(f'''
    {event.title}
    Начало - {event.start_time.strftime('%d %B %H:%M')}
    {event.program_description}
    Спикер - {event.speaker.username}
    Место проведения  - {event.location}
    ''')

    context.bot_data['speaker'] = event.speaker
    try:
        user = get_object_or_404(User, telegram_id=query.from_user.id)
        context.bot_data['user'] = user
    except Http404:
        user = None

    if user:
        keyboard = [
            [
                InlineKeyboardButton(
                    'Задать вопрос спикеру',
                    callback_data='ask_question'
                )
            ]
            if user.role == 'LISTENER' else [],
            [
                InlineKeyboardButton(
                    'Посмотреть вопросы слушателей',
                    callback_data='get_questions'
                )
            ]
            if user.role == 'SPEAKER' else [],
            [
                InlineKeyboardButton(
                    "Вернуться к списку мероприятий",
                    callback_data='menu'
                )
            ]
        ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    'Зарегистрироваться',
                    callback_data='register_user'
                )
            ]
        ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def register_user(update: Update, context: CallbackContext):
    query = update.callback_query
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
                'Некорректный формат ФИО. '
                'Пожалуйста, введите Фамилия Имя Отчество.'
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
                'Номер телефона некорректный. '
                'Пожалуйста, введите номер в формате +1234567890 или 1234567890.'
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
                'Адрес электронной почты некорректный. '
                'Пожалуйста, введите правильный адрес.'
            )
            return
        user_data['email'] = email
        events_keyboard = [
            [InlineKeyboardButton("Вернуться к списку мероприятий",
                                  callback_data='menu')]
        ]
        reply_markup = InlineKeyboardMarkup(events_keyboard)
        message.reply_text(
            f'Регистрация завершена. Ваши данные:'
            f'\nФИО: {user_data["fio"]}\nТелефон:'
            f' {user_data["phone"]}\nEmail: {user_data["email"]}',
            reply_markup=reply_markup
        )
        new_member = User(
            username=user_data["fio"],
            telegram_id=message.from_user.id,
            email=user_data["email"],
            phonenumber=user_data["phone"]
            )
        new_member.save()
        user_data.clear()


def ask_question(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
        data = query.data
        if data.startswith('ask_question'):
            context.user_data['step'] = 'ASK_QUESTION'
            query.message.reply_text('Задайте свой вопрос докладчику')


def save_question(update: Update, context: CallbackContext):
    message = update.message
    user_data = context.user_data

    if 'step' in user_data and user_data['step'] == 'ASK_QUESTION':
        question_text = message.text
        try:
            listener = User.objects.get(telegram_id=message.from_user.id)
            Question.objects.create(
                description=question_text,
                listener=listener,
                speaker=context.bot_data['speaker'],
                event=get_object_or_404(Event, id=context.bot_data['event']),
            )
            keyboard = [
                [InlineKeyboardButton(
                    "Вернуться к списку мероприятий",
                    callback_data='menu'
                )]
            ]
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Ваш вопрос успешно отправлен',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except User.DoesNotExist:
            message.reply_text(
                'Произошла ошибка при отправке вопроса. '
                'Пожалуйста, попробуйте снова.'
            )
        user_data.clear()


def handle_user_message(update: Update, context: CallbackContext):
    user_data = context.user_data

    if 'step' in user_data and user_data['step'] == 'ASK_QUESTION':
        save_question(update, context)
    else:
        register_user(update, context)


def get_questions(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    speaker = context.bot_data['user']
    event = get_object_or_404(Event, id=context.bot_data['event'])
    questions = Question.objects.filter(
        speaker=speaker.id,
        status=False,
        event=event
    )
    if questions.count() == 0:
        keyboard = [
            [InlineKeyboardButton(
                "Вернуться к списку мероприятий",
                callback_data='menu'
            )]
        ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='У вас нет неотвеченных вопросов',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [InlineKeyboardButton(
                'Ответить на вопрос',
                callback_data='answer_question'
                )],
            [InlineKeyboardButton(
                "Вернуться к списку мероприятий",
                callback_data='menu'
                )]
        ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Вам поступило {questions.count()} вопросf. Ответите?',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def answer_question(update: Update, context: CallbackContext):
    event = get_object_or_404(Event, id=context.bot_data['event'])
    question = random.choice(context.bot_data['user'].answer.filter(
        status=False,
        event=event
    ).select_related())
    context.bot_data['question'] = question
    keyboard = [
        [InlineKeyboardButton(
            'Следующий вопрос',
            callback_data='next_question'
        )],
        [InlineKeyboardButton(
            'Отметить как отвеченный',
            callback_data='status_question'
        )],
        [InlineKeyboardButton(
            "Вернуться к списку мероприятий",
            callback_data='menu'
        )],
    ]
    context.bot_data['question'] = question
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=question.description,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    message = update.effective_message
    context.bot.delete_message(
        chat_id=message.chat_id,
        message_id=message.message_id
    )


def get_answer(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'status_question':
        context.bot_data['question'].status = True
        context.bot_data['question'].save()
        try:
            return answer_question(update, context)
        except IndexError:
            return get_questions(update, context)
    elif query.data == 'next_question':
        try:
            return answer_question(update, context)
        except IndexError:
            return get_questions(update, context)


class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(
            CallbackQueryHandler(choose_events, pattern='menu')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(register_user, pattern='register_user')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(ask_question, pattern='ask_question')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(get_questions, pattern='get_questions')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(answer_question, pattern='answer_question')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(get_answer, pattern='next_question')
        )
        dispatcher.add_handler(
            CallbackQueryHandler(get_answer, pattern='status_question')
        )
        dispatcher.add_handler(
            MessageHandler(
                Filters.text & ~Filters.command,
                handle_user_message
            )
        )

        dispatcher.add_handler(
            CallbackQueryHandler(
                get_schedule_events
            )
        )

        updater.start_polling()
        updater.idle()
