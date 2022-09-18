import logging
import os

import music_tag
from orator import Model
from telegram.error import TelegramError
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, \
     Defaults, PicklePersistence
from telegram import Update, ReplyKeyboardMarkup, ChatAction, ParseMode, ReplyKeyboardRemove
from telegram import (
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
)

import localization as lp
from utils import translate_key_to, reset_user_data_context, generate_start_over_keyboard, \
create_user_directory, download_file, increment_usage_counter_for_user, delete_file, \
generate_module_selector_keyboard, generate_tag_editor_keyboard, generate_music_info

# from members.models import User

# from models.admin import Admin
from models.user import User
from dbconfig import db

Model.set_connection_resolver(db)

# BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN = "353909760:AAEvjTzsEpcW3XjMcFwtMFvPh6qE1g3nszk"
BOT_USERNAME = ""

logger = logging.getLogger()

# بعد از استارت نمایش ۲ دکمه بعنوان انتخاب زبان 
# اطلاعاتی به کار بر میچسبد مانند زبان که هر بار صبق زبان اطلاعات لود میشود
# زمانی که هندلری انجام میشود باید  همان مورد ارسال شود و پیغام اعتبار سنجی تحت اشتباه بودن ارسال نمیشود
# ۲ هندلر برای گرفتن آهنگ و موزیک وجود دارد
#  متاسفانه هندلر ها ولیدیشن ندارند

def command_start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username

    reset_user_data_context(context)

    user = User.where('user_id', '=', user_id).first()
    # user = 1

    update.message.reply_text(
        translate_key_to(lp.START_MESSAGE, context.user_data['language']),
        reply_markup=ReplyKeyboardRemove()
    )

    show_language_keyboard(update, context)

    if not user:
        new_user = User()
        new_user.user_id = user_id
        new_user.username = username
        new_user.number_of_files_sent = 0

        new_user.save()

        logger.info("A user with id %s has been started to use the bot.", user_id)

def show_language_keyboard(update: Update, _context: CallbackContext) -> None:
    language_button_keyboard = ReplyKeyboardMarkup(
        [
            ['🇬🇧 English', '🇮🇷 فارسی'],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    update.message.reply_text(
        "Please choose a language:\n\n"
        "لطفا زبان را انتخاب کنید:",
        reply_markup=language_button_keyboard,
    )


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

    user = User.where('user_id', '=', user_id).first()
    # user = 1
    user.language = user_data['language']
    user.push()

def handle_music_message(update: Update, context: CallbackContext) -> None:
    message = update.message
    user_id = update.effective_user.id
    user_data = context.user_data
    # این قسمت برای گرفتن موزیک
    music_duration = message.audio.duration
    # این قسمت برای گرفتن سایز موزیک
    music_file_size = message.audio.file_size
    # این قسمت برای گرفتن موزیک
    old_music_path = user_data['music_path']
    old_art_path = user_data['art_path']
    old_new_art_path = user_data['new_art_path']
    language = user_data['language']

    if music_duration >= 3600 and music_file_size > 48000000:
        message.reply_text(
            translate_key_to(lp.ERR_TOO_LARGE_FILE, language),
            reply_markup=generate_start_over_keyboard(language)
        )
        return

    # در حال تایپ
    context.bot.send_chat_action(
        chat_id=message.chat_id,
        action=ChatAction.TYPING
    )

    try:
        # ساخت دایرکتوری با ای دی کاربر برای ذخیره کردن موزیک
        create_user_directory(user_id)
    except OSError:
        message.reply_text(translate_key_to(lp.ERR_CREATING_USER_FOLDER, language))
        logger.error("Couldn't create directory for user %s", user_id, exc_info=True)
        return

    # بعد از ساخت دایرکتوری فایل دانلود میشود
    try:
        file_download_path = download_file(
            user_id=user_id,
            file_to_download=message.audio,
            file_type='audio',
            context=context
        )
    except ValueError:
        message.reply_text(
            translate_key_to(lp.ERR_ON_DOWNLOAD_AUDIO_MESSAGE, language),
            reply_markup=generate_start_over_keyboard(language)
        )
        logger.error("Error on downloading %s's file. File type: Audio", user_id, exc_info=True)
        return

    # در این قسمت فایل لود میشود
    try:
        music = music_tag.load_file(file_download_path)
    except (OSError, NotImplementedError):
        message.reply_text(
            translate_key_to(lp.ERR_ON_READING_TAGS, language),
            reply_markup=generate_start_over_keyboard(language)
        )
        logger.error(
            "Error on reading the tags %s's file. File path: %s",
            user_id,
            file_download_path,
            exc_info=True
        )
        return

    # چسباندن تگ های مورد نیاز
    reset_user_data_context(context)

    user_data['music_path'] = file_download_path
    user_data['art_path'] = ''
    user_data['music_message_id'] = message.message_id
    user_data['music_duration'] = message.audio.duration

    tag_editor_context = user_data['tag_editor']

    artist = music['artist']
    title = music['title']
    album = music['album']
    genre = music['genre']
    art = music['artwork']
    year = music.raw['year']
    disknumber = music.raw['disknumber']
    tracknumber = music.raw['tracknumber']

    if art:
        art_path = user_data['art_path'] = f"{file_download_path}.jpg"
        with open(art_path, 'wb') as art_file:
            art_file.write(art.first.data)

    tag_editor_context['artist'] = str(artist)
    tag_editor_context['title'] = str(title)
    tag_editor_context['album'] = str(album)
    tag_editor_context['genre'] = str(genre)
    tag_editor_context['year'] = str(year)
    tag_editor_context['disknumber'] = str(disknumber)
    tag_editor_context['tracknumber'] = str(tracknumber)

    show_module_selector(update, context)

    # تعداد ارسال فایل در دیتابیس ذخیره میشود
    increment_usage_counter_for_user(user_id=user_id)

    user = User.where('user_id', '=', user_id).first()
    user.username = update.effective_user.username
    user.push()

    # حذف فایل بعد از انجام 
    delete_file(old_music_path)
    delete_file(old_art_path)
    delete_file(old_new_art_path)

# این قسمت بعد از ارسال عکس انجام میشود
def handle_photo_message(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    message = update.message
    user_id = update.effective_user.id
    music_path = user_data['music_path']
    current_active_module = user_data['current_active_module']
    current_tag = user_data['tag_editor']['current_tag']
    lang = user_data['language']

    tag_editor_keyboard = generate_tag_editor_keyboard(lang)
# در صورتی که عکس مورد نظر حاوی تگ مورد نظر نباشد پیغمی مبنی بر چه تگی را میخواهی ویرایش کنی ارسال میشود
    if music_path:
        if current_active_module == 'tag_editor':
            if not current_tag or current_tag != 'album_art':
                reply_message = translate_key_to(lp.ASK_WHICH_TAG, lang)
                message.reply_text(reply_message, reply_markup=tag_editor_keyboard)
            else:
                try:
                    # در غیر این صورت عکس دانلود میشود
                    file_download_path = download_file(
                        user_id=user_id,
                        file_to_download=message.photo[len(message.photo) - 1],
                        file_type='photo',
                        context=context
                    )
                    # بعد از امجام تغییرات پیغام مورد نظر ارسال میشود
                    reply_message = f"{translate_key_to(lp.ALBUM_ART_CHANGED, lang)} " \
                                    f"{translate_key_to(lp.CLICK_PREVIEW_MESSAGE, lang)} " \
                                    f"{translate_key_to(lp.OR, lang).upper()} " \
                                    f"{translate_key_to(lp.CLICK_DONE_MESSAGE, lang).lower()}"
                                    # در این قسمت میتوان روی اسلش دان کلیکل کرد و موزیک را گرفت/done
                    user_data['new_art_path'] = file_download_path
                    message.reply_text(reply_message, reply_markup=tag_editor_keyboard)
                except (ValueError, BaseException):
                    message.reply_text(translate_key_to(lp.ERR_ON_DOWNLOAD_AUDIO_MESSAGE, lang))
                    logger.error(
                        "Error on downloading %s's file. File type: Photo",
                        user_id,
                        exc_info=True
                    )
                    return
    else:
        reply_message = translate_key_to(lp.DEFAULT_MESSAGE, lang)
        message.reply_text(reply_message, reply_markup=ReplyKeyboardRemove())

# بعد از ارسال موزیک این قسمت فراخوانی میشود
def show_module_selector(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data
    context.user_data['current_active_module'] = ''
    lang = user_data['language']

    module_selector_keyboard = generate_module_selector_keyboard(lang)

    update.message.reply_text(
        translate_key_to(lp.ASK_WHICH_MODULE, lang),
        reply_to_message_id=update.effective_message.message_id,
        reply_markup=module_selector_keyboard
    )

# زمانیکه شما میخواهید تگ های یک موزیک را ویرایش کنید به این قسمت وارد میشود
def handle_music_tag_editor(update: Update, context: CallbackContext) -> None:
    message = update.message
    user_data = context.user_data
    art_path = user_data['art_path']
    lang = user_data['language']

    user_data['current_active_module'] = 'tag_editor'

    tag_editor_context = user_data['tag_editor']
    tag_editor_context['current_tag'] = ''

# این قسمت دکمه ای شیشه ای برای ویرایش را میسازد
    tag_editor_keyboard = generate_tag_editor_keyboard(lang)

# این قسمت همه اطلاعات موزیک را میفرستد
    if art_path:
        with open(art_path, 'rb') as art_file:
            message.reply_photo(
                photo=art_file,
                caption=generate_music_info(tag_editor_context).format(f"\n🆔 {BOT_USERNAME}"),
                reply_to_message_id=update.effective_message.message_id,
                reply_markup=tag_editor_keyboard,
                parse_mode='Markdown'
            )
    else:
        message.reply_text(
            generate_music_info(tag_editor_context).format(f"\n🆔 {BOT_USERNAME}"),
            reply_to_message_id=update.effective_message.message_id,
            reply_markup=tag_editor_keyboard
        )

# بعد از زدن دکمه عکس آلبوم این تابع اعمال میشود
def prepare_for_album_art(update: Update, context: CallbackContext) -> None:
    if len(context.user_data) == 0:
        message_text = translate_key_to(lp.DEFAULT_MESSAGE, context.user_data['language'])
    else:
        context.user_data['tag_editor']['current_tag'] = 'album_art'
        message_text = translate_key_to(lp.ASK_FOR_ALBUM_ART, context.user_data['language'])

    update.message.reply_text(message_text)

def main():
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN, timeout=120)
    persistence = PicklePersistence('persistence_storage')

    updater = Updater(BOT_TOKEN, persistence=persistence, defaults=defaults)
    add_handler = updater.dispatcher.add_handler

    add_handler(CommandHandler('start', command_start))

    ############################
    # ماژول های عملیات روی موزیک
    ############################
    add_handler(MessageHandler(
        (Filters.regex('^(🎵 Tag Editor)$') | Filters.regex('^(🎵 تغییر تگ ها)$')),
        handle_music_tag_editor)
    )
    
    ############################
    # زمانیکه دکمه آلبوم عکس زده میشود این قسمت فراخوانی میشود
    ############################
    add_handler(MessageHandler(
        (Filters.regex('^(🖼 Album Art)$') | Filters.regex('^(🖼 عکس آلبوم)$')),
        prepare_for_album_art)
    )

    #################
    # File Handlers #
    #################
    # این هندلر برای گرفتن موزیک است
    add_handler(MessageHandler(Filters.audio, handle_music_message))
    # این هندلر برای گرفتن عکس است
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