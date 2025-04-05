import telebot
from telebot import types
import json
import os
import random
import openai

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

bot = telebot.TeleBot(TOKEN)

# Load user data
try:
    with open("user_data.json", "r", encoding="utf-8") as f:
        user_data = json.load(f)
except FileNotFoundError:
    user_data = {}

CATEGORY_MAP = {
    "Базовая": "basic",
    "Средняя": "medium",
    "Суперприз": "super"
}

CATEGORY_EMOJIS = {
    "basic": "🔹 Basic:",
    "medium": "🔹 Medium:",
    "super": "🔹 Super:"
}

# Save user data
def save_user_data():
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {}
    save_user_data()
    bot.reply_to(message, "Привет! Я бот-награда! Используй /addreward чтобы добавить награду.")

# Add reward command
@bot.message_handler(commands=['addreward'])
def add_reward(message):
    markup = types.InlineKeyboardMarkup()
    for label in CATEGORY_MAP.keys():
        markup.add(types.InlineKeyboardButton(text=label, callback_data=f"select_category:{label}"))
    bot.send_message(message.chat.id, "Выбери категорию награды:", reply_markup=markup)

# Category selected
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_category:"))
def handle_category_selection(call):
    category_label = call.data.split(":")[1]
    user_id = str(call.from_user.id)
    user_data[user_id] = user_data.get(user_id, {})
    user_data[user_id]["selected_category"] = CATEGORY_MAP.get(category_label, "basic")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Задать самому", callback_data="manual"),
        types.InlineKeyboardButton("Получить от ИИ", callback_data="ai")
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Хочешь задать награду сам или получить варианты от ИИ?",
                          reply_markup=markup)

# Manual or AI reward generation
@bot.callback_query_handler(func=lambda call: call.data in ["manual", "ai"])
def handle_reward_option(call):
    user_id = str(call.from_user.id)
    user_data[user_id] = user_data.get(user_id, {})
    user_data[user_id]["method"] = call.data
    save_user_data()

    if call.data == "manual":
        msg = bot.send_message(call.message.chat.id, "Напиши свою награду в формате: \n /addreward [текст награды]")
        bot.register_next_step_handler(msg, save_manual_reward)
    else:
        send_ai_suggestions(call.message)

# Generate AI suggestions
def generate_ai_rewards():
    prompt = "Придумай 3 короткие награды, которые человек может себе позволить после фокус-сессии. Примеры: 'чашка кофе', '10 минут музыки', 'отдых с котом'. Только список, без пояснений."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message["content"].strip()
    return text.split("\n")

# Send 3 suggestions and save to user_data
ai_suggestions = {}

def send_ai_suggestions(message):
    user_id = str(message.chat.id)
    category = user_data.get(user_id, {}).get("selected_category", "basic")

    try:
        suggestions = generate_ai_rewards()
        ai_suggestions[user_id] = suggestions

        reply = "Вот 3 варианта награды. Выбери одну или нажми 'ещё':\n"
        for i, s in enumerate(suggestions, 1):
            reply += f"{i}. {s}\n"

        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton("1", callback_data="select_1"),
            types.InlineKeyboardButton("2", callback_data="select_2"),
            types.InlineKeyboardButton("3", callback_data="select_3"),
            types.InlineKeyboardButton("🔄 Ещё", callback_data="more")
        ]
        markup.add(*buttons[:3])
        markup.add(buttons[3])

        bot.send_message(message.chat.id, reply, reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при генерации наград: " + str(e))

# Handle AI choice or 'more'
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_") or call.data == "more")
def handle_ai_choice(call):
    user_id = str(call.from_user.id)
    if call.data == "more":
        send_ai_suggestions(call.message)
        return

    index = int(call.data[-1]) - 1
    reward = ai_suggestions.get(user_id, [])[index]
    category = user_data.get(user_id, {}).get("selected_category", "basic")

    user_data[user_id].setdefault("rewards", {})
    user_data[user_id]["rewards"].setdefault(category, []).append(reward)
    save_user_data()

    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, f"✅ Награда сохранена: {reward}")

# Save manually entered reward
@bot.message_handler(func=lambda msg: msg.text.startswith("/addreward "))
def save_manual_reward(message):
    user_id = str(message.from_user.id)
    category = user_data.get(user_id, {}).get("selected_category", "basic")
    reward_text = message.text[len("/addreward "):].strip()

    user_data[user_id].setdefault("rewards", {})
    user_data[user_id]["rewards"].setdefault(category, []).append(reward_text)
    save_user_data()

    bot.reply_to(message, f"✅ Награда сохранена: {reward_text}")

# List rewards
@bot.message_handler(commands=["listrewards"])
def list_rewards(message):
    user_id = str(message.from_user.id)
    rewards = user_data.get(user_id, {}).get("rewards", {})

    text = "🎁 Твои награды:\n"
    for cat in ["basic", "medium", "super"]:
        text += f"\n{CATEGORY_EMOJIS[cat]}\n"
        entries = rewards.get(cat, [])
        if entries:
            for r in entries:
                text += f"— {r}\n"
        else:
            text += "— пока пусто\n"

    bot.reply_to(message, text)

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
