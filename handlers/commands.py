from telebot.types import Message

def register_command_handlers(bot, user_data):
    @bot.message_handler(commands=['start'])
    def handle_start(message: Message):
        bot.reply_to(message,
            "👋 Привет! Я Rewardy — бот-награда, который помогает тебе оставаться сфокусированным и не забывать про отдых и удовольствие.\n\n"
            "📍 Как это работает:\n"
            "- Фокусируйся 30 минут (помидор 🍅)\n"
            "- Получай награду после каждого помидора: здоровую или дофаминовую 🎯\n"
            "- Каждые 4 помидора — улучшенная награда\n"
            "- За каждый помидор получаешь 1 фокус-поинт. 30 поинтов = супернаграда! 💎\n\n"
            "✨ Команды:\n"
            "/addreward — добавить награду\n"
            "/myrewards — список моих наград\n"
            "/timer — начать фокус-сессию\n"
            "/status — проверить статус\n"
            "/cancel — отменить таймер\n"
            "/buysuper — потратить 30 поинтов на супернаграду")

    @bot.message_handler(commands=['help'])
    def handle_help(message: Message):
        bot.reply_to(message,
            "Доступные команды:\n"
            "/start — инструкция\n"
            "/help — помощь\n"
            "/addreward — добавить награду\n"
            "/myrewards — мои награды\n"
            "/timer — фокус-сессия\n"
            "/status — статус таймера и поинтов\n"
            "/cancel — отменить таймер\n"
            "/buysuper — потратить 30 фокус-поинтов")
