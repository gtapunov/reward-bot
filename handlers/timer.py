from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import random
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
        user_data[user_id] = user_data.get(user_id, {})
        if "start_time" in user_data[user_id]:
            start = datetime.fromisoformat(user_data[user_id]["start_time"])
            elapsed = datetime.utcnow() - start
            remaining = timedelta(seconds=20) - elapsed
            if remaining.total_seconds() > 0:
                m = int(remaining.total_seconds() // 60)
                s = int(remaining.total_seconds() % 60)
                points = user_data[user_id].get("focus_points", 0)
                pomos = user_data[user_id].get("pomodoro_count", 0)
                status_text = f"⏳ Осталось: {m} мин {s} сек\n🍅 Помидоров в этой сессии: {pomos}\n⭐️ Focus Points: {points}"
                bot.reply_to(message, status_text)
            else:
                # Завершение таймера и выдача награды
                count = user_data[user_id].get("pomodoro_count", 0) + 1
                user_data[user_id]["pomodoro_count"] = count
                user_data[user_id]["focus_points"] = user_data[user_id].get("focus_points", 0) + 1
                del user_data[user_id]["start_time"]

                # Определение категории
                category = "medium" if count % 4 == 0 else "basic"
                sub = "healthy" if random.random() < 0.7 else "dopamine"
                key = f"{category}_{sub}"

                # Выбор награды
                rewards = user_data[user_id].get("rewards", {}).get(key, [])
                if rewards:
                    reward = random.choice(rewards)
                    bot.send_message(message.chat.id, f"🏆 Награда за фокус-сессию: {reward}")
                else:
                    bot.send_message(message.chat.id, f"🏆 Фокус-сессия завершена! Но у тебя нет наград категории {category} ({sub}) 😢")

                # Кнопки: перерыв или завершение
                markup = InlineKeyboardMarkup()
                if count % 4 == 0:
                    markup.add(InlineKeyboardButton("🛌 Перерыв 20 минут", callback_data="break_20"))
                else:
                    markup.add(InlineKeyboardButton("☕ Перерыв 5 минут", callback_data="break_5"))
                markup.add(InlineKeyboardButton("🚫 Завершить фокусирование", callback_data="end_focus"))
                bot.send_message(message.chat.id, "Что делаем дальше?", reply_markup=markup)

                save_user_data()
        else:
            bot.reply_to(message, "Нет активного таймера.")
