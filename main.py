# Rewardy MVP Bot (Python + pyTelegramBotAPI + OpenAI)
# Фокус-таймер с наградами и AI-генерацией

import os
from dotenv import load_dotenv
load_dotenv()

import telebot
import threading
import random
import json
import time
from datetime import datetime, timedelta
import openai
from telebot import types

API_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(API_TOKEN)

try:
    with open("user_data.json", "r") as f:
        user_data = json.load(f)
except:
    user_data = {}

def save_data():
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

timers = {}
start_times = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "base": 0,
            "mid": 0,
            "super": 0,
            "rewards": {"basic": [], "medium": [], "super": []},
            "selected_category": None,
            "ai_suggestions": []
        }
        save_data()
    bot.reply_to(message, "Привет! Я бот Rewardy. Пиши /pomodoro, чтобы начать фокус-сессию.")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "📘 Команды:\n/pomodoro – начать фокус-сессию на 30 мин\n/status – посмотреть прогресс\n/cancel – отменить текущий таймер\n/addreward – добавить награду\n/listrewards – посмотреть награды\n/help – показать эту справку")

@bot.message_handler(commands=['status'])
def handle_status(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        bot.reply_to(message, "Напиши /start сначала.")
        return
    data = user_data[user_id]
    response = f"Твой прогресс:\n- Базовых очков: {data['base']}\n- До средней награды: {15 - data['mid']}\n- До суперприза: {30 - data['super']}"
    if user_id in start_times:
        elapsed = datetime.now() - start_times[user_id]
        remaining = timedelta(minutes=30) - elapsed
        minutes, seconds = divmod(int(remaining.total_seconds()), 60)
        response += f"\n⏳ Осталось: {minutes} мин {seconds} сек"
    else:
        response += "\n⏳ Сейчас нет активного помидора."
    bot.reply_to(message, response)

@bot.message_handler(commands=['cancel'])
def cancel_timer(message):
    user_id = str(message.chat.id)
    if user_id in timers:
        timers[user_id].cancel()
        del timers[user_id]
        if user_id in start_times:
            del start_times[user_id]
        bot.reply_to(message, "⛔️ Таймер отменён.")
    else:
        bot.reply_to(message, "Нет активного таймера.")

def send_reward(user_id):
    if user_id in timers:
        del timers[user_id]
    if user_id in start_times:
        del start_times[user_id]

    data = user_data[user_id]
    data["base"] += 1
    data["mid"] += 1
    data["super"] += 1

    reward = None
    if data["super"] >= 30:
        rewards = data["rewards"]["super"]
        if rewards:
            reward = random.choice(rewards)
            bot.send_message(user_id, f"🔥🔥🔥 Супернаграда: {reward}")
        else:
            bot.send_message(user_id, "🔥🔥🔥 Помидор завершён! Но у тебя нет супернаград.")
        data["super"] = 0
        data["mid"] = 0

    elif data["mid"] >= 15:
        rewards = data["rewards"]["medium"]
        if rewards:
            reward = random.choice(rewards)
            bot.send_message(user_id, f"🎯 Средняя награда: {reward}")
        else:
            bot.send_message(user_id, "🎯 Помидор завершён! Но у тебя нет средних наград.")
        data["mid"] = 0

    elif data["base"] % 3 == 0:
        rewards = data["rewards"]["basic"]
        if rewards:
            reward = random.choice(rewards)
            bot.send_message(user_id, f"🚀 Базовая награда: {reward}")
        else:
            bot.send_message(user_id, "🚀 Помидор завершён! Но у тебя нет базовых наград.")
    else:
        bot.send_message(user_id, "✅ Помидор завершён! Продолжай в том же духе 💪")

    save_data()

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

@bot.message_handler(commands=['pomodoro'])
def handle_pomodoro(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        send_welcome(message)

    if user_id in timers:
        bot.reply_to(message, "⚠️ Уже идёт фокус-сессия. Используй /cancel для отмены.")
        return

    bot.reply_to(message, "⏳ Отлично! Таймер на 30 минут запущен.")
    timer = threading.Timer(1800, send_reward, args=[user_id])
    timers[user_id] = timer
    start_times[user_id] = datetime.now()
    timer.start()

# --- AI reward generation ---
def generate_ai_rewards():
    prompt = "Предложи 3 коротких и приятных награды за фокус-сессию. Только список:"
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    return [line.strip("0123456789. ") for line in text.split("\n") if line.strip()][:3]

@bot.message_handler(commands=['addreward'])
def handle_addreward(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Базовая", "Средняя", "Суперприз")
    bot.send_message(message.chat.id, "Выбери категорию награды:", reply_markup=markup)
    bot.register_next_step_handler(message, ask_reward_input_method)

def ask_reward_input_method(message):
    user_id = str(message.chat.id)
    if message.text not in ["Базовая", "Средняя", "Суперприз"]:
        bot.send_message(message.chat.id, "Некорректная категория. Попробуй снова.")
        return
    user_data[user_id]["selected_category"] = message.text.lower()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Задать самому", "Получить от ИИ")
    bot.send_message(message.chat.id, "Хочешь задать награду сам или получить варианты от ИИ?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_reward_option)

def handle_reward_option(message):
    user_id = str(message.chat.id)
    if message.text == "Задать самому":
        bot.send_message(message.chat.id, "Введи текст награды:")
        bot.register_next_step_handler(message, save_manual_reward)
    elif message.text == "Получить от ИИ":
        suggestions = generate_ai_rewards()
        user_data[user_id]["ai_suggestions"] = suggestions
        numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
        markup = types.InlineKeyboardMarkup()
        for i in range(3):
            markup.add(types.InlineKeyboardButton(f"{i+1}", callback_data=f"select_ai_{i}"))
        markup.add(types.InlineKeyboardButton("🔁 Ещё", callback_data="more_ai"))
        bot.send_message(message.chat.id, f"Вот 3 варианта награды. Выбери одну или нажми 'ещё':\n{numbered}", reply_markup=markup)
        save_data()
    else:
        bot.send_message(message.chat.id, "Некорректный выбор. Попробуй снова.")

def save_manual_reward(message):
    user_id = str(message.chat.id)
    category = user_data[user_id].get("selected_category")
    text = message.text.strip()
    if category and text:
        user_data[user_id]["rewards"][category].append(text)
        save_data()
        bot.send_message(message.chat.id, f"✅ Награда добавлена в {category}.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_ai_"))
def handle_ai_selection(call):
    user_id = str(call.message.chat.id)
    index = int(call.data.split("_")[-1])
    category = user_data[user_id].get("selected_category")
    suggestion = user_data[user_id].get("ai_suggestions", [])[index]
    user_data[user_id]["rewards"][category].append(suggestion)
    save_data()
    bot.send_message(user_id, f"✅ Награда добавлена: {suggestion}")

@bot.callback_query_handler(func=lambda call: call.data == "more_ai")
def handle_more_ai(call):
    user_id = str(call.message.chat.id)
    suggestions = generate_ai_rewards()
    user_data[user_id]["ai_suggestions"] = suggestions
    numbered = "\n".join([f"{i+1}. {s}" for i, s in enumerate(suggestions)])
    markup = types.InlineKeyboardMarkup()
    for i in range(3):
        markup.add(types.InlineKeyboardButton(f"{i+1}", callback_data=f"select_ai_{i}"))
    markup.add(types.InlineKeyboardButton("🔁 Ещё", callback_data="more_ai"))
    bot.edit_message_text(f"Вот 3 варианта награды. Выбери одну или нажми 'ещё':\n{numbered}", call.message.chat.id, call.message.message_id, reply_markup=markup)
    save_data()

print("Bot is running...")
bot.infinity_polling()
