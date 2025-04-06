import os
import json
import telebot
from dotenv import load_dotenv
from handlers.commands import register_command_handlers

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Load user data from file
try:
    with open("user_data.json", "r", encoding="utf-8") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

# Save user data
def save_user_data():
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

# Register command handlers
register_command_handlers(bot, user_data, save_user_data)

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
