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
import openai
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(API_TOKEN)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
temp_rewards = {}  # временное хранилище сгенерированных наград

# --- Команда /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
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

# --- Команда /addreward ---
@bot.message_handler(commands=['addreward'])
def handle_addreward(message):
    user_id = str(message.chat.id)
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
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Базовая", callback_data="cat_basic"),
        InlineKeyboardButton("Средняя", callback_data="cat_medium"),
        InlineKeyboardButton("Суперприз", callback_data="cat_super")
    )
    bot.send_message(message.chat.id, "Выбери категорию награды:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def select_reward_method(call):
    user_id = str(call.message.chat.id)
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
    category = call.data.split("_")[1]
    user_data[user_id]["selected_category"] = category
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Задать самому", callback_data="manual"),
        InlineKeyboardButton("Получить от ИИ", callback_data="ai")
    )
    bot.send_message(call.message.chat.id, "Хочешь придумать сам или получить идеи от ИИ?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["manual", "ai"])
def handle_reward_option(call):
    user_id = str(call.message.chat.id)
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
    category = user_data[user_id].get("selected_category")
    if call.data == "manual":
        bot.send_message(call.message.chat.id, f"Напиши текст награды для категории {category}:")
        bot.register_next_step_handler(call.message, lambda msg: save_manual_reward(msg, category))
    else:
        suggestions = generate_ai_rewards()
        temp_rewards[user_id] = suggestions
        show_ai_suggestions(call.message.chat.id, suggestions)

def generate_ai_rewards():
    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Ты помощник, который генерирует простые награды за работу."},
            {"role": "user", "content": "Придумай 3 приятных награды для пользователя, завершившего фокус-сессию. Выведи их в формате: 1. ... 2. ... 3. ..."}
        ],
        model="gpt-3.5-turbo"
    )
    rewards_text = response.choices[0].message.content.strip()
    suggestions = [r.strip("-• 1234567890.") for r in rewards_text.split("\n") if r.strip()]
    return suggestions[:3]

def show_ai_suggestions(chat_id, options):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(f"1️⃣ {options[0][:20]}", callback_data="pick_0"),
        InlineKeyboardButton(f"2️⃣ {options[1][:20]}", callback_data="pick_1"),
        InlineKeyboardButton(f"3️⃣ {options[2][:20]}", callback_data="pick_2")
    )
    markup.row(InlineKeyboardButton("🔄 Ещё", callback_data="more_ai"))
    bot.send_message(chat_id, "Вот 3 варианта награды. Выбери одну или нажми 'ещё':", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pick_"))
def handle_pick_reward(call):
    user_id = str(call.message.chat.id)
    if user_id not in user_data:
        return
    idx = int(call.data.split("_")[1])
    category = user_data[user_id].get("selected_category")
    reward = temp_rewards.get(user_id, [])[idx]
    user_data[user_id]["rewards"][category].append(reward)
    save_data()
    bot.send_message(call.message.chat.id, f"✅ Награда добавлена в категорию {category}!")

@bot.callback_query_handler(func=lambda call: call.data == "more_ai")
def handle_more_ai(call):
    user_id = str(call.message.chat.id)
    suggestions = generate_ai_rewards()
    temp_rewards[user_id] = suggestions
    show_ai_suggestions(call.message.chat.id, suggestions)

@bot.message_handler(func=lambda message: True)
def save_manual_reward(message, category):
    user_id = str(message.chat.id)
    reward = message.text.strip()
    user_data[user_id]["rewards"][category].append(reward)
    save_data()
    bot.send_message(message.chat.id, f"✅ Награда добавлена в категорию {category}!")

# --- Запуск ---
print("Bot is running...")
bot.infinity_polling()
