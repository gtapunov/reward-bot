import telebot
import os
import time

from dotenv import load_dotenv
from threading import Thread
from storage import load_user_data
from handlers.commands import register_command_handlers
from handlers.timer import register_timer_handlers
from handlers.rewards import register_reward_handlers
from handlers.timer import check_timers

# Загрузка .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

# Удаляем Webhook, чтобы не было конфликта с polling
bot.remove_webhook()

# Загружаем данные
user_data = load_user_data()

# Регистрируем обработчики
register_command_handlers(bot, user_data)
register_timer_handlers(bot, user_data)
register_reward_handlers(bot, user_data)

# Запускаем бота
if __name__ == "__main__":
    print("Bot is running...")

    # Поток для проверки таймеров (фокус и перерывы)
    timer_thread = Thread(target=check_timers, args=(bot, user_data), daemon=True)
    timer_thread.start()

    bot.infinity_polling()
