from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from handlers.rewards import pick_random_reward
import random
import json
import threading
import time
from storage import save_user_data

def register_timer_handlers(bot, user_data):

    @bot.message_handler(commands=["timer"])
    def start_timer(message: Message):
        user_id = str(message.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["start_time"] = datetime.utcnow().isoformat()
        save_user_data(user_data)
        bot.reply_to(message, "⏱ Таймер на 30 минут запущен!")

    @bot.message_handler(commands=["cancel"])
    def cancel_timer(message: Message):
        user_id = str(message.from_user.id)
        if "start_time" in user_data.get(user_id, {}):
            del user_data[user_id]["start_time"]
            save_user_data(user_data)
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
            remaining = timedelta(seconds=60) - elapsed
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
                
                # Определение категории награды
                category = "medium" if count % 4 == 0 else "basic"
                sub = "healthy" if random.random() < 0.7 else "dopamine"
                key = f"{category}_{sub}"
                
                # Выбор награды
                rewards = user_data.get(user_id, {}).get("rewards", {}).get(key, [])
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

                save_user_data(user_data)
        else:
            points = user_data[user_id].get("focus_points", 0)
            pomos = user_data[user_id].get("pomodoro_count", 0)
            status_text = f"⏳ Нет активного таймера.\n🍅 Помидоров в этой сессии: {pomos}\n⭐ Focus Points: {points}"
            bot.reply_to(message, status_text)

    @bot.callback_query_handler(func=lambda call: call.data in ["break_5", "break_20"])
    def handle_break(call):
        user_id = str(call.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        now = datetime.utcnow()
    
        break_minutes = 5 if call.data == "break_5" else 20
        break_end = now + timedelta(minutes=break_minutes)
        user_data[user_id]["break_until"] = break_end.isoformat()
        user_data[user_id]["break_done"] = False
        user_data[user_id]["break_start_time"] = now.isoformat()
    
        save_user_data(user_data)
    
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⏹ Завершить перерыв", callback_data="end_break"))
    
        bot.edit_message_text(
            f"😌 Перерыв на {break_minutes} минут начался!\n"
            f"Можешь завершить его досрочно 👇",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == "end_break")
    def handle_end_break(call):
        user_id = str(call.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id].pop("break_until", None)
    
        save_user_data(user_data)
    
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("▶️ Начать следующую фокус-сессию", callback_data="next_focus"),
            InlineKeyboardButton("⛔️ Завершить фокусирование", callback_data="end_focus")
        )
    
        bot.edit_message_text(
            "🔔 Перерыв завершён. Что дальше?",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == "next_focus")
    def handle_next_focus(call):
        user_id = str(call.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["start_time"] = datetime.utcnow().isoformat()
        save_user_data(user_data)
        
        bot.edit_message_text(
            "🧠 Новая фокус-сессия началась! 30 минут тишины...",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data == "end_focus")
    def handle_end_focus(call):
        user_id = str(call.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id].pop("start_time", None)
        user_data[user_id]["pomodoro_count"] = 0  # сбрасываем
        save_user_data(user_data)
        
        bot.edit_message_text(
            "✅ Фокус-сессия завершена. Отличная работа!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id)

def check_timers(bot, user_data):
    print("[DEBUG] check_timers запущен...")

    while True:
        time.sleep(10)
        now = datetime.utcnow()
        print(f"[DEBUG] Цикл проверки таймеров — {now.isoformat()}")

        for user_id, data in user_data.items():
            print(f"[DEBUG] Проверка пользователя {user_id} — данные: {data}")

            # Проверка завершения фокус-сессии
            if "start_time" in data and not data.get("session_active"):
                start = datetime.fromisoformat(data["start_time"])
                elapsed = now - start
                print(f"[DEBUG] Прошло времени: {elapsed.total_seconds()} сек")

                if elapsed >= timedelta(seconds=60):  # заменено для теста
                    print("[DEBUG] ⏰ Фокус-сессия завершена! Обрабатываем...")

                    del data["start_time"]
                    data["session_active"] = False
                    data["pomodoro_count"] = data.get("pomodoro_count", 0) + 1
                    data["focus_points"] = data.get("focus_points", 0) + 1

                    is_medium = data["pomodoro_count"] % 4 == 0
                    reward_type = "medium" if is_medium else "basic"
                    reward_category = "healthy" if random.random() < 0.7 else "dopamine"
                    reward_text, reward_type, reward_category = pick_random_reward(user_data, user_id, data["pomodoro_count"])

                    text = f"🎯 Фокус-сессия завершена!\nТы заработал награду: {reward_text}"
                    markup = InlineKeyboardMarkup()
                    btn_text = "Начать перерыв 20 минут" if is_medium else "Начать перерыв 5 минут"
                    callback = "break_20" if is_medium else "break_5"
                    markup.add(InlineKeyboardButton(btn_text, callback_data=callback))

                    bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
                    save_user_data(user_data)

            # Проверка завершения перерыва
            if "break_start_time" in data and not data.get("break_done"):
                break_start = datetime.fromisoformat(data["break_start_time"])
                break_duration = 20 if data.get("long_break") else 5
                elapsed = now - break_start

                print(f"[DEBUG] Проверка перерыва — прошло {elapsed.total_seconds()} сек")  # <--- ДЛЯ ДЕБАГА

                if elapsed >= timedelta(minutes=break_duration):
                    print("[DEBUG] Перерыв завершён! Отправляю сообщение...")
                    data["break_done"] = True
                    print("[DEBUG] ⏳ Перерыв завершён!")
                    text = "⏳ Перерыв завершён!"
                    markup = InlineKeyboardMarkup()
                    markup.add(
                        InlineKeyboardButton("Начать следующую фокус-сессию", callback_data="next_focus"),
                        InlineKeyboardButton("Завершить фокусирование", callback_data="end_focus")
                    )
                    bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
                    save_user_data(user_data)
