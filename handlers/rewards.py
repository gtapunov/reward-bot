from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import openai
import os
import json
from storage import save_user_data

openai.api_key = os.getenv("OPENAI_API_KEY")

CATEGORY_MAP = {
    "Базовая": "basic",
    "Средняя": "medium",
    "Суперприз": "super"
}

def register_reward_handlers(bot, user_data):
    ai_suggestions = {}

    def save_user_data():
        with open("user_data.json", "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

    @bot.message_handler(commands=["addreward"])
    def add_reward(message: Message):
        markup = InlineKeyboardMarkup()
        for label in CATEGORY_MAP:
            markup.add(InlineKeyboardButton(label, callback_data=f"category:{label}"))
        bot.send_message(message.chat.id, "Выбери категорию награды:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("category:"))
    def handle_category_selection(call: CallbackQuery):
        category_label = call.data.split(":")[1]
        user_id = str(call.from_user.id)
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["selected_category"] = CATEGORY_MAP[category_label]
        save_user_data()

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Добавить свою", callback_data="method:manual"),
            InlineKeyboardButton("Получить идеи от ИИ", callback_data="method:ai")
        )
        bot.edit_message_text("Выбери способ добавления награды:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("method:"))
    def handle_method_selection(call: CallbackQuery):
        method = call.data.split(":")[1]
        user_id = str(call.from_user.id)
        if method == "manual":
            msg = bot.send_message(call.message.chat.id, "Напиши свою награду:")
            bot.register_next_step_handler(msg, handle_manual_reward)
        elif method == "ai":
            send_ai_suggestions(call.message)

    def handle_manual_reward(message: Message):
        user_id = str(message.from_user.id)
        category = user_data[user_id]["selected_category"]
        reward = message.text.strip()
        user_data[user_id].setdefault("rewards", {}).setdefault(category, []).append(reward)
        save_user_data(user_data)
        bot.reply_to(message, f"✅ Награда сохранена: {reward}")

    def send_ai_suggestions(message: Message):
        user_id = str(message.chat.id)
        category = user_data[user_id]["selected_category"]
        prompt = "Придумай 3 короткие награды, которые человек может себе позволить после фокус-сессии. Только список, без пояснений."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            suggestions = response.choices[0].message["content"].strip().split("\n")
            ai_suggestions[user_id] = suggestions

            text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
            markup = InlineKeyboardMarkup()
            for i in range(3):
                markup.add(InlineKeyboardButton(str(i+1), callback_data=f"select:{i}"))
            markup.add(InlineKeyboardButton("🔄 Ещё", callback_data="more"))
            bot.send_message(message.chat.id, "Выбери награду или запроси ещё идеи:\n" + text, reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при генерации наград: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("select:") or call.data == "more")
    def handle_ai_choice(call: CallbackQuery):
        user_id = str(call.from_user.id)
        if call.data == "more":
            send_ai_suggestions(call.message)
            return
        index = int(call.data.split(":")[1])
        reward = ai_suggestions[user_id][index]
        category = user_data[user_id]["selected_category"]
        user_data[user_id].setdefault("rewards", {}).setdefault(category, []).append(reward)
        save_user_data(user_data)
        bot.send_message(call.message.chat.id, f"✅ Награда сохранена: {reward}")
