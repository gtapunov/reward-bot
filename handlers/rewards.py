from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import openai
import os
import json
from storage import save_user_data

openai.api_key = os.getenv("OPENAI_API_KEY")

CATEGORY_MAP = {
    "Базовая": "basic",
    "Средняя": "medium",
    "Супернаграда": "super"
}

SUBCATEGORY_MAP = {
    "Здоровая": "healthy",
    "Дофаминовая": "dopamine"
}

CATEGORY_LABELS = {
    "basic_healthy": "Базовые (Здоровые)",
    "basic_dopamine": "Базовые (Дофаминовые)",
    "medium_healthy": "Средние (Здоровые)",
    "medium_dopamine": "Средние (Дофаминовые)",
    "super": "Супернаграды"
}

def register_reward_handlers(bot, user_data):
    ai_suggestions = {}

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

        # Если выбрана "Суперприз", сразу показать варианты добавления
        if category_label == "Суперприз":
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("Добавить свою", callback_data="method:manual"),
                InlineKeyboardButton("Получить идеи от ИИ", callback_data="method:ai")
            )
            bot.edit_message_text("Выбери способ добавления награды:",
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=markup)
        else:
            # Показать тип награды: здоровая / дофаминовая
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🧘 Здоровая", callback_data="type:healthy"),
                InlineKeyboardButton("📱 Дофаминовая", callback_data="type:dopamine")
            )
            bot.edit_message_text("Уточни тип награды:",
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=markup)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("type:"))
    def handle_type_selection(call: CallbackQuery):
        reward_type = call.data.split(":")[1]
        user_id = str(call.from_user.id)
        user_data[user_id]["selected_type"] = reward_type
        save_user_data()

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Добавить свою", callback_data="method:manual"),
            InlineKeyboardButton("Получить идеи от ИИ", callback_data="method:ai")
        )
        bot.send_message(call.message.chat.id, "Выбери способ добавления награды:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("subcategory:"))
    def handle_subcategory_selection(call: CallbackQuery):
        subcategory_label = call.data.split(":")[1]
        user_id = str(call.from_user.id)
        sub = SUBCATEGORY_MAP[subcategory_label]
        category = user_data[user_id]["selected_category"]
        user_data[user_id]["selected_category"] = f"{category}_{sub}"
        save_user_data(user_data)
        show_input_method_selection(call.message)

    def show_input_method_selection(msg):
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Задать самому", callback_data="method:manual"),
            InlineKeyboardButton("Предложение от ИИ", callback_data="method:ai")
        )
        bot.send_message(msg.chat.id, "Выбери способ добавления награды:", reply_markup=markup)

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
        reward_type = user_data[user_id].get("selected_type")
        reward = message.text.strip()

        if category == "super":
            user_data[user_id].setdefault("rewards", {}).setdefault("super", []).append(reward)
        else:
            user_data[user_id].setdefault("rewards", {}).setdefault(category, {}).setdefault(reward_type, []).append(reward)

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
            raw_lines = response.choices[0].message["content"].strip().split("\n")
            suggestions = [line.lstrip("0123456789. ").strip() for line in raw_lines if line.strip()]
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

    if user_id not in ai_suggestions:
        bot.send_message(call.message.chat.id, "⚠️ Я не нашёл предложений. Пожалуйста, сначала запроси идеи от ИИ.")
        return

    try:
        index = int(call.data.split(":")[1])
        reward = ai_suggestions[user_id][index]
        category = user_data[user_id]["selected_category"]
        subcategory = user_data[user_id].get("selected_subcategory")

        key = f"{category}_{subcategory}" if subcategory else category
        user_data[user_id].setdefault("rewards", {}).setdefault(key, []).append(reward)
        save_user_data(user_data)
        bot.send_message(call.message.chat.id, f"✅ Награда сохранена: {reward}")
    except (IndexError, ValueError):
        bot.send_message(call.message.chat.id, "⚠️ Что-то пошло не так. Попробуй снова.")

    @bot.message_handler(commands=["myrewards"])
    def list_rewards(message: Message):
        user_id = str(message.from_user.id)
        rewards = user_data.get(user_id, {}).get("rewards", {})

        if not rewards:
            bot.reply_to(message, "У тебя пока нет наград. Добавь их через /addreward")
            return

        text = "🎁 Твои награды:\n"
        for cat in ["basic_healthy", "basic_dopamine", "medium_healthy", "medium_dopamine", "super"]:
            entries = rewards.get(cat, [])
            if entries:
                label = CATEGORY_LABELS.get(cat, cat)
                text += f"\n{label}:\n"
                for i, r in enumerate(entries, 1):
                    clean = r.lstrip("1234567890. ").strip()
                    text += f"{i}. {clean}\n"
        bot.reply_to(message, text)
