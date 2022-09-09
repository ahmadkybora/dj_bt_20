import logging
import os

import music_tag
from telegram.error import TelegramError
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, \
     Defaults, PicklePersistence
from telegram import Update, ReplyKeyboardMarkup, ChatAction, ParseMode, ReplyKeyboardRemove
from telegram import (
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
)

import localization as lp
from utils import translate_key_to

# from members.models import User

#BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN = "353909760:AAEvjTzsEpcW3XjMcFwtMFvPh6qE1g3nszk"
def command_start():
    pass

def handle_music_message():
    pass

def handle_photo_message():
    pass

def set_language(update: Update, context: CallbackContext) -> None:
    lang = update.message.text.lower()
    user_data = context.user_data
    user_id = update.effective_user.id

    if "english" in lang:
        user_data['language'] = 'en'
    elif "فارسی" in lang:
        user_data['language'] = 'fa'

    update.message.reply_text(translate_key_to(lp.LANGUAGE_CHANGED, user_data['language']))
    update.message.reply_text(
        translate_key_to(lp.START_OVER_MESSAGE, user_data['language']),
        reply_markup=ReplyKeyboardRemove()
    )

    # user = User.where('user_id', '=', user_id).first()
    # user.language = user_data['language']
    # user.push()

def main():
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN, timeout=120)
    persistence = PicklePersistence('persistence_storage')

    updater = Updater(BOT_TOKEN, persistence=persistence, defaults=defaults)
    add_handler = updater.dispatcher.add_handler

    add_handler(CommandHandler('start', command_start))

    #################
    # File Handlers #
    #################
    add_handler(MessageHandler(Filters.audio, handle_music_message))
    add_handler(MessageHandler(Filters.photo, handle_photo_message))

    ############################
    # Change Language Handlers #
    ############################
    add_handler(MessageHandler(Filters.regex('^(🇬🇧 English)$'), set_language))
    add_handler(MessageHandler(Filters.regex('^(🇮🇷 فارسی)$'), set_language))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()