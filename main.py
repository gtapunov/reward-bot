import os
from flask import Flask, request
from dotenv import load_dotenv
import telebot

# Загрузка .env переменных
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Инициализация
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# Роут для Telegram webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def receive_update():
    print("✅ Получен запрос от Telegram")
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

# Проверка живости
@app.route("/", methods=["GET"])
def index():
    return "Rewardy bot is alive!", 200

# Обработчики команд
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "👋 Привет! Это Rewardy — твой бот-награда!")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "🛠 Доступные команды: /start /help")

# УСТАНОВКА WEBHOOK — В САМОМ КОНЦЕ
bot.remove_webhook()
webhook_url = f"{BASE_URL}/{TOKEN}"
print(f"📡 Устанавливаю webhook: {webhook_url}")
bot.set_webhook(url=webhook_url)
