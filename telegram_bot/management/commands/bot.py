from django.core.management.base import BaseCommand
from telegram import Update
from MeetUpPlanner import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackContext


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я ваш бот.')


def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        updater = Updater(settings.TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(MessageHandler(
            Filters.text & ~Filters.command, echo)
        )

        updater.start_polling()
        updater.idle()
