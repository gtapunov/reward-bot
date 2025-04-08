from telebot.types import Message
from datetime import datetime, timedelta
import json

def register_timer_handlers(bot, user_data):
    def save_user_data():
        with open("user_data.json", "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

    @bot.message_handler(commands=["timer"])
    def start_timer(message: Message):
        user_id = str(message.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["start_time"] = datetime.utcnow().isoformat()
        save_user_data()
        bot.reply_to(message, "⏱ Таймер на 30 минут запущен!")

    @bot.message_handler(commands=["cancel"])
    def cancel_timer(message: Message):
        user_id = str(message.from_user.id)
        if "start_time" in user_data.get(user_id, {}):
            del user_data[user_id]["start_time"]
            save_user_data()
            bot.reply_to(message, "❌ Таймер отменён.")
        else:
            bot.reply_to(message, "Нет активного таймера.")

    @bot.message_handler(commands=["status"])
    def timer_status(message: Message):
        user_id = str(message.from_user.id)
        if "start_time" in user_data.get(user_id, {}):
            start = datetime.fromisoformat(user_data[user_id]["start_time"])
            elapsed = datetime.utcnow() - start
            remaining = timedelta(minutes=30) - elapsed
            if remaining.total_seconds() > 0:
                m = int(remaining.total_seconds() // 60)
                s = int(remaining.total_seconds() % 60)
                bot.reply_to(message, f"Осталось: {m} мин {s} сек")
            else:
                bot.reply_to(message, "⏰ Время вышло! Заверши фокус-сессию и получи награду.")
        else:
            bot.reply_to(message, "Нет активного таймера.")
