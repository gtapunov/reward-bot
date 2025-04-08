from telebot.types import Message

def register_command_handlers(bot, user_data):
    @bot.message_handler(commands=['start'])
    def handle_start(message: Message):
        bot.reply_to(message, "Привет! Я Rewardy — бот-награда. Используй /addreward, чтобы добавить награды, или /timer, чтобы начать фокус-сессию.")

    @bot.message_handler(commands=['help'])
    def handle_help(message: Message):
        bot.reply_to(message, "Доступные команды:\n/start — приветствие\n/help — помощь\n/timer — фокус-сессия\n/cancel — отмена таймера\n/status — статус\n/addreward — добавить награду\n/myrewards — мои награды")
