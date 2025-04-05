import os
from flask import Flask, request
import telebot
from telebot import types
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Инициализируем Flask и TeleBot
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Обработка Webhook-запросов от Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    print("✅ Получен запрос от Telegram")
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Простая GET-проверка
@app.route("/", methods=["GET"])
def index():
    return "✅ Rewardy работает через Flask + webhook", 200

# Команды
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Это Rewardy — твой бот для наград.")

@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "Доступные команды: /start /help")

# Устанавливаем webhook
bot.remove_webhook()
webhook_url = f"{BASE_URL}/{TOKEN}"
print(f"📡 Устанавливаю webhook: {webhook_url}")
bot.set_webhook(url=webhook_url)
