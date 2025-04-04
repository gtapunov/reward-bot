# Rewardy MVP Bot (Python + pyTelegramBotAPI)
# Функционал: /pomodoro запускает таймер 30 мин, затем отправляется награда

import os
from dotenv import load_dotenv
load_dotenv()

import telebot
import threading
import random
import json
import time
from datetime import datetime, timedelta

API_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# --- Счётчики пользователей и награды ---
try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except:
    user_data = {}

def save_data():
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# --- Активные таймеры ---
timers = {}
start_times = {}
# --- Обработка команды /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    print(f"[LOG] /start от {message.chat.first_name} ({user_id})")
    if user_id not in user_data:
        user_data[user_id] = {
            "base": 0,
            "mid": 0,
            "super": 0,
            "rewards": {
                "basic": [],
                "medium": [],
                "super": []
            }
        }
        save_data()
    bot.reply_to(message, "Привет! Я бот Rewardy. Пиши /pomodoro, чтобы начать фокус-сессию.")

# --- Команда /help ---
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "📘 Команды:\n/pomodoro – начать фокус-сессию на 30 мин\n/status – посмотреть прогресс\n/cancel – отменить текущий таймер (если передумал)\n/addreward – добавить награду в список\n/listrewards – посмотреть свои награды\n/help – показать эту справку")

# --- Команда /status ---
@bot.message_handler(commands=['status'])
def handle_status(message):
    user_id = str(message.chat.id)
    print(f"[LOG] /status от {message.chat.first_name} ({user_id})")
    if user_id not in user_data:
        bot.reply_to(message, "Я ещё не знаю тебя. Напиши /start сначала.")
        return
    data = user_data[user_id]
    response = f"Твой прогресс:\n- Базовых очков: {data['base']}\n- До средней награды: {15 - data['mid']}\n- До суперприза: {30 - data['super']}"
    if user_id in start_times:
        elapsed = datetime.now() - start_times[user_id]
        remaining = timedelta(minutes=30) - elapsed
        minutes, seconds = divmod(int(remaining.total_seconds()), 60)
        response += f"\n⏳ Осталось до конца помидора: {minutes} мин {seconds} сек"
    else:
        response += "\n⏳ Сейчас нет активного помидора."
    bot.reply_to(message, response)

# --- Команда /cancel ---
@bot.message_handler(commands=['cancel'])
def cancel_timer(message):
    user_id = str(message.chat.id)
    if user_id in timers:
        timers[user_id].cancel()
        del timers[user_id]
        if user_id in start_times:
            del start_times[user_id]
        bot.reply_to(message, "⛔️ Таймер отменён. Помидор не будет засчитан.")
        print(f"[LOG] Таймер отменён для {user_id}")
    else:
        bot.reply_to(message, "Нет активного таймера, который можно отменить.")

# --- Функция отправки награды ---
def send_reward(user_id):
    if user_id in timers:
        del timers[user_id]
    if user_id in start_times:
        del start_times[user_id]

    data = user_data[user_id]
    print(f"[LOG] Завершён помидор у {user_id} | base: {data['base']}, mid: {data['mid']}, super: {data['super']}")

    data["base"] += 1
    data["mid"] += 1
    data["super"] += 1

    reward = None
    if data["super"] >= 30:
        rewards = data["rewards"]["super"]
        if rewards:
            reward = random.choice(rewards)
            bot.send_message(user_id, f"🔥🔥🔥 Помидор завершён! Твоя супернаграда: {reward}")
            print(f"[LOG] Супернаграда: {reward}")
        else:
            bot.send_message(user_id, "🔥🔥🔥 Помидор завершён! Но у тебя нет супернаград 😅 Добавь их с помощью /addreward.")
        data["super"] = 0
        data["mid"] = 0

    elif data["mid"] >= 15:
        rewards = data["rewards"]["medium"]
        if rewards:
            reward = random.choice(rewards)
            bot.send_message(user_id, f"🎯 Помидор завершён! Твоя средняя награда: {reward}")
            print(f"[LOG] Средняя награда: {reward}")
        else:
            bot.send_message(user_id, "🎯 Помидор завершён! Но у тебя нет средних наград 😅 Добавь их с помощью /addreward.")
        data["mid"] = 0

elif data["base"] % 3 == 0:
    rewards = data["rewards"]["basic"]
    if rewards:
        reward = random.choice(rewards)
        bot.send_message(user_id, f"🚀 Помидор завершён! Твоя базовая награда: {reward}")
        print(f"[LOG] Базовая награда: {reward}")
    else:
        bot.send_message(user_id, "🚀 Помидор завершён! Но у тебя нет базовых наград 😅 Добавь их с помощью /addreward.")
else:
    bot.send_message(user_id, "✅ Помидор завершён! Продолжай в том же духе 💪")
    print("[LOG] Награда не выдана (не кратно 3, не достигнуты пороги)")

save_data()

# --- Команда /addreward ---
@bot.message_handler(commands=['addreward'])
def handle_addreward(message):
user_id = str(message.chat.id)
parts = message.text.split(maxsplit=2)

if len(parts) < 3:
    bot.reply_to(message, "Формат: /addreward [basic|medium|super] [текст награды]")
    return

category = parts[1].lower()
reward_text = parts[2].strip()

if category not in ["basic", "medium", "super"]:
    bot.reply_to(message, "Категория должна быть: basic, medium или super.")
    return

if user_id not in user_data:
    bot.reply_to(message, "Сначала напиши /start, чтобы я тебя запомнил.")
    return

user_data[user_id]["rewards"][category].append(reward_text)
save_data()
bot.reply_to(message, f"✅ Награда добавлена в список {category}!")

# --- Команда /listrewards ---
@bot.message_handler(commands=['listrewards'])
def handle_listrewards(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        bot.reply_to(message, "Напиши /start сначала.")
        return

    rewards = user_data[user_id]["rewards"]
    response = "🎁 Твои награды:\n"
    for cat in ["basic", "medium", "super"]:
        response += f"\n🔹 {cat.capitalize()}:\n"
        if rewards[cat]:
            for i, r in enumerate(rewards[cat], 1):
                response += f"{i}. {r}\n"
        else:
            response += "— пока пусто\n"

    bot.reply_to(message, response)

# --- Команда /pomodoro ---
@bot.message_handler(commands=['pomodoro'])
def handle_pomodoro(message):
    user_id = str(message.chat.id)
    print(f"[LOG] /pomodoro от {message.chat.first_name} ({user_id})")
    if user_id not in user_data:
        user_data[user_id] = {
            "base": 0,
            "mid": 0,
            "super": 0,
            "rewards": {
                "basic": [],
                "medium": [],
                "super": []
            }
        }
        save_data()

    if user_id in timers:
        bot.reply_to(message, "⚠️ У тебя уже идёт фокус-сессия! Дождись её окончания или используй /cancel.")
        print(f"[LOG] Попытка запустить второй таймер у {user_id} — отклонена")
        return

    bot.reply_to(message, "⏳ Отлично! Таймер на 30 минут запущен. Я напомню тебе, когда время выйдет.")
    timer = threading.Timer(1800, send_reward, args=[user_id])
    timers[user_id] = timer
    start_times[user_id] = datetime.now()
    print("[LOG] Таймер запущен на 30 минут")
    timer.start()

# --- Запуск ---
print("Bot is running...")
bot.infinity_polling()