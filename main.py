from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import ssym 
from urllib.parse import urlparse
import os
import tempfile
import shutil

def is_supported(url: str) -> bool:
    domain = urlparse(url).netloc
    return domain in ['music.yandex.ru', 'soundcloud.com', 'open.spotify.com']

def platform(url: str) -> bool:
    domain = urlparse(url).netloc
    return domain

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_id = update.message.message_id
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="<i><b>🤗 Привет, я бот для скачивания музыки популярных платформ.</b></i>\n\n<b>Сейчас ты можешь прислать мне ссылку на трек/плейлист/альбом!</b>\n\n<code>Поддерживаемые платформы: YandexMusic/SoundCloud/Spotify</code>\n\n<b>/menu - Главное Меню</b>",
        reply_to_message_id=message_id,
        parse_mode="HTML"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Телеграм Разработчика", url="https://t.me/dreviax")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "<b>😲 Прилшлите ссылку боту и он сам найдет и скачает трек, плейлист или альбом</b>\n\n<b><i>Внимание все треки из плейлистов/альбомов будут загружены по отдельности! Не пугайтесь</i></b>\n\n\n<code>🙏 Обратная связь с разработчиком при ошибках:</code>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def process_music_link(update: Update, url: str, is_supported: bool, url_platform: str):
    if not is_supported:
        await update.message.reply_text("<b>❌ Эта платформа не поддерживается!</b>", parse_mode="HTML")
        return
        
    await update.message.reply_text(f'<b>🤖 Начинаю загрузку <a href="{url}">контента</a></b>', parse_mode="HTML")
    
    files = []
    try:
        if url_platform == "soundcloud.com":
            files = ssym.download_soundcloud_url(url)
        elif url_platform == "music.yandex.ru":
            files = ssym.download_yandex_music_url(url)
        elif url_platform == "open.spotify.com":
            files = ssym.download_spotify_url(url)
        
        if not files:
            raise Exception("<b>💀 Контент не найден или недоступен</b>")
            
        success_count = 0
        for file_path in files:
            try:
                with open(file_path, 'rb') as file:
                    await update.message.reply_document(
                        document=file,
                        filename=os.path.basename(file_path),
                        caption=f"<b>🎵 {os.path.basename(file_path)[:-4]}</b>" if len(files) > 1 else None,
                        parse_mode="HTML"
                    )
                success_count += 1
            except Exception as e:
                print(f"<b>💀 Ошибка отправки файла {file_path}: {e}</b>")
                continue
        
        if success_count == 0:
            raise Exception("<b>💀 Не удалось отправить ни одного трека</b>")
            
    except Exception as e:
        error_msg = (
            f"<b>🤕 Произошла ошибка:</b>\n"
            f"<code><pre>{str(e)}</pre></code>\n\n"
            "<b>👽 Возможные причины:</b>\n"
            "1) Плейлист/альбом приватный или удалён\n"
            "2) Ограничения авторских прав\n"
            "3) Технические проблемы на сервере\n\n"
            "<b><i>Вы можете попробовать скачать отдельные треки вручную</i></b>"
        )
        await update.message.reply_text(error_msg, parse_mode="HTML")
    finally:
        # Очистка временных файлов
        if files:
            temp_dirs = set()
            for file_path in files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        temp_dir = os.path.dirname(file_path)
                        if temp_dir.startswith(tempfile.gettempdir()):
                            temp_dirs.add(temp_dir)
                    except Exception as e:
                        print(f"<b>💀 Ошибка удаления файла {file_path}: {e}</b>")
            
            for temp_dir in temp_dirs:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    print(f"<b>💀 Ошибка удаления директории {temp_dir}: {e}</b>")

    if files:
        await update.message.reply_text(
            "<b>✅ Завершено!</b>\n"
            "<b><i>👽 Спасибо за использование бота. По вопросам: @dreviax</i></b>",
            parse_mode="HTML"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if user_text.startswith(('http://', 'https://')):
        result = is_supported(user_text)
        url_platform = platform(user_text)
        await process_music_link(update, user_text, result, url_platform)
    else:
        await update.message.reply_text("<b>😡 Кажется... Это не ссылка!</b>\n🤗 Пришлите ссылку на контент)", parse_mode="HTML")

app = Application.builder().token("7507590797:AAEbrW1rS5IrPOqFetLiTSGKUNeQSRERMQ0").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("menu", menu))
app.run_polling()