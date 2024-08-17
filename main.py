import os
from dotenv import load_dotenv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
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

# Словарь с предопределёнными ответами
REPLIES = {
    "привет": "Здравствуйте!",
    "здравствуйте": "Здравствуйте!",
}

# Словарь для хранения состояния пользователей
user_states = {}

# Функция для создания кнопок в зависимости от состояния
def create_buttons(state):
    keyboard = []

    if state == 'start':
        keyboard = [
            [InlineKeyboardButton("Наши соц.сети", callback_data='massengers'),
             InlineKeyboardButton("Наш сайт", callback_data='site')],
            [InlineKeyboardButton("Расчет стоимости страхования", callback_data='summStraxovki'),
             InlineKeyboardButton("Связаться с оператором", callback_data='contact_operator')]
        ]
    elif state == 'massengers':
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data='start')]
        ]
    elif state == 'site':
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data='start')]
        ]
    elif state == 'summStraxovki':
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data='start')]
        ]
    elif state == 'contact_operator':
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data='start')]
        ]

    return InlineKeyboardMarkup(keyboard)

# Функция-обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:  # Проверяем, что update содержит message
        user_id = update.effective_user.id
        user_states[user_id] = 'start'  # Устанавливаем начальное состояние
        reply_text = 'Здравствуйте! Я ваш персональный помощник по вопросам страхования. Выберите один из вариантов, и я подберу оптимальное решение для вас.'
        await update.message.reply_text(reply_text, reply_markup=create_buttons('start'))

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
        user_id = update.effective_user.id
        current_state = user_states.get(user_id, 'start')
        await update.message.reply_text(reply, reply_markup=create_buttons(current_state))
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

# Функции для обработки нажатий на кнопки
async def handle_massengers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = 'massengers'
    await query.edit_message_text(text="Наши соц.сети: [Ссылка на соц.сети]", reply_markup=create_buttons('massengers'))

async def handle_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = 'site'
    await query.edit_message_text(text="Наш сайт: [Ссылка на сайт]", reply_markup=create_buttons('site'))

async def handle_summStraxovki(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = 'summStraxovki'
    await query.edit_message_text(text="Расчет стоимости страхования: [Ссылка на расчет]", reply_markup=create_buttons('summStraxovki'))

async def handle_contact_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_states[user_id] = 'contact_operator'
    await query.edit_message_text(text="Переход на оператора. Пожалуйста, подождите...", reply_markup=create_buttons('contact_operator'))

# Определяем обработчики кнопок
BUTTON_HANDLERS = {
    'massengers': handle_massengers,
    'site': handle_site,
    'summStraxovki': handle_summStraxovki,
    'contact_operator': handle_contact_operator,
}

# Обработчик кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    callback_data = query.data

    # Проверяем, если это кнопка "Назад"
    if callback_data == 'start':
        user_states[user_id] = 'start'
        await query.edit_message_text(text="Выберите один из вариантов:", reply_markup=create_buttons('start'))
    else:
        handler = BUTTON_HANDLERS.get(callback_data)
        if handler:
            await handler(update, context)  # Передаем оба параметра
        else:
            logger.warning(f"Неизвестная команда кнопки: {callback_data}")

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

# Запуск скрипта
if __name__ == '__main__':
    main()
