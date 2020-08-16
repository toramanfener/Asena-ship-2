import logging, os
from telegram.ext import Updater, CommandHandler
from telegram import Bot, Update, Message

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

token = os.environ['TELEGRAM_TOKEN']

def start(bot: Bot, update: Update):
    text = 'Hello! SHIPPERING is a bot that will choose a couple of the day in your chat.\n\n Use /help for more info.'
    update.message.reply_text(text)


def main():
    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()