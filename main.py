from telebot import TeleBot
from dotenv import load_dotenv
import os
from handlers.commands import register_command_handlers
from handlers.rewards import register_reward_handlers
from handlers.timer import register_timer_handlers
from storage import load_user_data

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

user_data = load_user_data()

register_command_handlers(bot, user_data)
register_reward_handlers(bot, user_data)
register_timer_handlers(bot, user_data)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
