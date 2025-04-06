from datetime import datetime, timedelta
from telebot import types

def register_command_handlers(bot, user_data, save_user_data):

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.reply_to(message, "Привет! Я Rewardy — бот, который помогает тебе награждать себя после фокус-сессий. Команды: /timer — начать таймер, /cancel — отменить, /status — статус таймера")

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        bot.reply_to(message, "Я помогаю тебе работать сфокусированно и не забывать про награды.\n\nКоманды:\n/start — приветствие\n/help — помощь\n/timer — начать таймер\n/cancel — отменить таймер\n/status — статус таймера")

    @bot.message_handler(commands=['timer'])
    def start_timer(message):
        user_id = str(message.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["start_time"] = datetime.utcnow().isoformat()
        save_user_data()
        bot.reply_to(message, "⏱ Таймер на 30 минут запущен! Я напомню, когда время истечёт.")

    @bot.message_handler(commands=['cancel'])
    def cancel_timer(message):
        user_id = str(message.from_user.id)
        if user_id in user_data and "start_time" in user_data[user_id]:
            del user_data[user_id]["start_time"]
            save_user_data()
            bot.reply_to(message, "❌ Таймер отменён.")
        else:
            bot.reply_to(message, "Нет активного таймера.")

    @bot.message_handler(commands=['status'])
    def timer_status(message):
        user_id = str(message.from_user.id)
        if user_id in user_data and "start_time" in user_data[user_id]:
            start_time = datetime.fromisoformat(user_data[user_id]["start_time"])
            elapsed = datetime.utcnow() - start_time
            remaining = timedelta(minutes=30) - elapsed
            if remaining.total_seconds() > 0:
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                bot.reply_to(message, f"⏳ Осталось времени: {mins} мин {secs} сек")
            else:
                bot.reply_to(message, "⏰ Время вышло! Заверши фокус-сессию и получи награду.")
        else:
            bot.reply_to(message, "Нет активного таймера.")
