from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import openai
import random
import os
import json
from storage import save_user_data

openai.api_key = os.getenv("OPENAI_API_KEY")

user_states = {}

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
        category = CATEGORY_MAP[category_label]
    
        user_data[user_id] = user_data.get(user_id, {})
        user_data[user_id]["selected_category"] = category
        # Стираем старую подкатегорию, если была
        user_data[user_id].pop("selected_subcategory", None)
    
        save_user_data(user_data)
    
        if category in ["basic", "medium"]:
            # Показываем кнопки дофаминовая / здоровая
            markup = InlineKeyboardMarkup()
            for sub in SUBCATEGORY_MAP:
                markup.add(InlineKeyboardButton(sub, callback_data=f"subcategory:{sub}"))
            bot.edit_message_text(
                "Уточни категорию награды:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        else:
            # Если супернаграда — сразу идём к выбору способа
            show_input_method_selection(call.message)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("type:"))
    def handle_type_selection(call: CallbackQuery):
        reward_type = call.data.split(":")[1]
        user_id = str(call.from_user.id)
        user_data[user_id]["selected_type"] = reward_type
        save_user_data(user_data)

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
    
        user_data[user_id]["selected_category"] = category
        user_data[user_id]["selected_subcategory"] = sub  # 💡 Вот эта строка была пропущена
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
        category = user_data[user_id].get("selected_category")
        subcategory = user_data[user_id].get("selected_subcategory")
    
        if not category:
            bot.reply_to(message, "Ошибка: категория не указана.")
            return
    
        rewards = message.text.strip().split('\n')  # <-- вот тут вся магия
    
        key = f"{category}_{subcategory}" if category != "super" else "super"
        user_data[user_id].setdefault("rewards", {})
        if key not in user_data[user_id]["rewards"] or not isinstance(user_data[user_id]["rewards"][key], list):
            user_data[user_id]["rewards"][key] = []
    
        user_data[user_id]["rewards"][key].extend(rewards)  # добавляем сразу все
    
        save_user_data(user_data)
        bot.reply_to(message, f"✅ Добавлено {len(rewards)} наград!")

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
    
        index = int(call.data.split(":")[1])
        suggestions = ai_suggestions.get(user_id)
        if not suggestions or index >= len(suggestions):
            bot.send_message(call.message.chat.id, "Ошибка: не могу найти награду.")
            return
    
        reward = suggestions[index]
        category = user_data[user_id].get("selected_category")
        subcategory = user_data[user_id].get("selected_subcategory")
    
        if not category:
            bot.send_message(call.message.chat.id, "Ошибка: категория не указана.")
            return
    
        key = f"{category}_{subcategory}" if category != "super" else "super"
    
        user_data[user_id].setdefault("rewards", {})
        if key not in user_data[user_id]["rewards"] or not isinstance(user_data[user_id]["rewards"][key], list):
            user_data[user_id]["rewards"][key] = []
    
        user_data[user_id]["rewards"][key].append(reward)
    
        save_user_data(user_data)
        bot.send_message(call.message.chat.id, f"✅ Награда сохранена: {reward}")

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

    @bot.message_handler(commands=["editreward"])
    def start_edit_reward(message):
        user_id = str(message.from_user.id)
        user_states[user_id] = {"step": "choose_category"}
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🟢 Базовые", callback_data="edit_basic"))
        markup.add(InlineKeyboardButton("🟡 Средние", callback_data="edit_medium"))
        bot.send_message(message.chat.id, "Выберите категорию награды:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
    def handle_edit_category(call):
        user_id = str(call.from_user.id)
        category = call.data.replace("edit_", "")
        if category in ["basic", "medium"]:
            # Выбор подкатегории
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💪 Здоровые", callback_data="edit_healthy"))
            markup.add(InlineKeyboardButton("🎉 Дофаминовые", callback_data="edit_dopamine"))
    
            bot.edit_message_text("Выберите подкатегорию:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    
        else:
            # Если супернаграда — сразу показываем список наград
            rewards = user_data.get(user_id, {}).get("rewards", {}).get("super", [])
    
        if not rewards:
            bot.send_message(call.message.chat.id, "❗️ У тебя нет супернаград.")
            user_states.pop(user_id, None)
            return
    
        reward_list = "\n".join(f"{i+1}. {r}" for i, r in enumerate(rewards))
        bot.send_message(call.message.chat.id, f"Вот список супернаград:\n\n{reward_list}\n\nНапиши номер награды, которую хочешь удалить.")
    
        user_states[user_id].update({"step": "await_number", "key": "super"})

    @bot.callback_query_handler(func=lambda call: call.data in ["edit_healthy", "edit_dopamine"])
    def handle_edit_sub(call):
        user_id = str(call.from_user.id)
        sub = call.data.replace("edit_", "")
        state = user_states.get(user_id, {})
        category = state.get("category")
    
        key = f"{category}_{sub}"
        rewards = user_data.get(user_id, {}).get("rewards", {}).get(key, [])
    
        if not rewards:
            bot.send_message(call.message.chat.id, f"⚠️ У тебя нет наград категории {category}, подкатегории {sub}")
            user_states.pop(user_id, None)
            return
    
        reward_list = "\n".join([f"{i+1}. {r}" for i, r in enumerate(rewards)])
        bot.send_message(call.message.chat.id, f"Вот список наград:\n{reward_list}\n\nНапиши номер награды, которую хочешь удалить.")
        
        user_states[user_id].update({"step": "await_number", "key": key})

    @bot.message_handler(func=lambda message: str(message.from_user.id) in user_states and user_states[str(message.from_user.id)]["step"] == "await_number")
    def delete_reward_by_number(message):
        user_id = str(message.from_user.id)
        state = user_states[user_id]
        key = state["key"]
        rewards = user_data.get(user_id, {}).get("rewards", {}).get(key, [])
        
        try:
            index = int(message.text.strip()) - 1
            if 0 <= index < len(rewards):
                removed = rewards.pop(index)
                save_user_data(user_data)
                bot.reply_to(message, f"✅ Награда '{removed}' удалена!")
            else:
                bot.reply_to(message, "❌ Неверный номер.")
        except ValueError:
            bot.reply_to(message, "❌ Введи, пожалуйста, номер награды.")
        
        user_states.pop(user_id, None)

def pick_random_reward(user_data, user_id, count):
    """
    Выбирает случайную награду в зависимости от номера помидора.
    count — это номер текущего помидора (после увеличения счётчика).
    """
    category = "medium" if count % 4 == 0 else "basic"
    subcategory = "healthy" if random.random() < 0.7 else "dopamine"
    key = f"{category}_{subcategory}"

    rewards = user_data.get(user_id, {}).get("rewards", {}).get(key, [])
    if not rewards:
        return "⚠️ У тебя нет наград категории", category, subcategory

    return random.choice(rewards), category, subcategory
