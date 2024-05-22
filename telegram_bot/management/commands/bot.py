from django.core.management.base import BaseCommand
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from MeetUpPlanner import settings
from telegram.ext import Updater, CommandHandler, CallbackContext


def start(update: Update, context: CallbackContext) -> None:
    full_name = update.message.from_user.full_name

    initial_message_text = (
        f"Привет, {full_name}. Я PyMeetBot — твой помощник на Мероприятия! 🎉\n"
        "Я помогу тебе задавать вопросы докладчикам, следить за программой и "
        "получать уведомления."
    )
    event_details_text = (
        "Мероприятие пройдет ..."
    )

    registration_keyboard = [
        [InlineKeyboardButton("Зарегистрироваться", callback_data='register')]
    ]
    reply_markup = InlineKeyboardMarkup(registration_keyboard)

    update.message.reply_text(initial_message_text)
    update.message.reply_text(event_details_text, reply_markup=reply_markup)


class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start))

        updater.start_polling()
        updater.idle()
