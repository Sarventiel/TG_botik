import os
from dotenv import load_dotenv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import pymorphy2
from pymorphy2 import MorphAnalyzer

# Загружаем переменные окружения
load_dotenv()

# Получаем токен из переменной окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Проверяем, что токен загружен корректно
if not TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализируем pymorphy2
morph = MorphAnalyzer()

# Словарь с предопределёнными ответами (с использованием лемматизированных слов)
REPLIES = {
    "привет": "Здравствуйте! Как я могу помочь вам сегодня?",
    "дело": "Спасибо, у меня всё хорошо! А как у вас?",
    "уметь": "Я умею отвечать на ваши вопросы и помогать в различных ситуациях!"
}

# Кнопки для сообщений
def start_buttons():
    keyboard = [
        [InlineKeyboardButton("Информация", callback_data='info')],
        [InlineKeyboardButton("Помощь", callback_data='help')],
        [InlineKeyboardButton("Связаться с оператором", callback_data='contact_operator')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция-обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_text = 'Здравствуйте! Я ваш персональный помощник по вопросам страхования. Выберите один из вариантов, и я подберу оптимальное решение для вас.'
    await update.message.reply_text(reply_text, reply_markup=start_buttons())

# Функция-обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text.lower()
        logger.info(f"Получено сообщение: {user_message}")

        # Лемматизация сообщения
        tokens = user_message.split()
        lemmatized_tokens = [morph.parse(token)[0].normal_form for token in tokens]

        # Ищем соответствие с предопределёнными ответами
        reply = None
        for token in lemmatized_tokens:
            if token in REPLIES:
                reply = REPLIES[token]
                break

        if reply is None:
            reply = "Я не знаю ответа на ваш вопрос. Могу перевести на оператора."

        # Отправляем ответ с кнопками
        await update.message.reply_text(reply, reply_markup=start_buttons())
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

# Функции для обработки нажатий на кнопки
async def handle_info(query):
    await query.edit_message_text(text="Это информация о нашем сервисе...", reply_markup=start_buttons())

async def handle_help(query):
    await query.edit_message_text(text="Выберите, чем я могу вам помочь:", reply_markup=start_buttons())

async def handle_contact_operator(query):
    await query.edit_message_text(text="Переход на оператора. Пожалуйста, подождите...", reply_markup=start_buttons())

# Обработчик кнопок
BUTTON_HANDLERS = {
    'info': handle_info,
    'help': handle_help,
    'contact_operator': handle_contact_operator,
}

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие на кнопку

    handler = BUTTON_HANDLERS.get(query.data)
    if handler:
        await handler(query)
    else:
        logger.warning(f"Неизвестная команда кнопки: {query.data}")

# Функция для запуска бота
def main():
    logger.info("Запуск бота...")
    # Создаем объект Application и передаем ему токен вашего бота.
    application = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))

    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Регистрируем обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button))

    # Запускаем бота
    logger.info("Бот запущен и готов принимать сообщения.")
    application.run_polling()

    logger.info("Бот завершил работу.")

# Запуск скрипта
if __name__ == '__main__':
    main()
