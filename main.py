import os
import json
from flask import Flask, request
import telebot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Flask app
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# Flask route for Telegram webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "", 200

# Simple route to check if the app is alive
@app.route("/", methods=["GET"])
def index():
    return "✅ Bot is running", 200

# Example command
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я жив и работаю через webhook 🙌")

# Set webhook
bot.remove_webhook()
bot.set_webhook(url=f"https://reward-bot-fpli.onrender.com/{TOKEN}")
