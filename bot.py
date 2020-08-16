import logging
import os
import json
import random
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

token = os.getenv('TELEGRAM_TOKEN')


def setup_shippering_file(update: Update, context: CallbackContext):
    if update.effective_chat.type != 'private':
        # initialize to 0 shipping counter if the file is empty
        chat_administrators = context.bot.get_chat_administrators(chat_id=update.effective_chat.id)
        with open('counters.json', 'r+') as counters_fp:
            try:
                counters = json.load(counters_fp)
            except json.JSONDecodeError as e:
                logging.warning(e)
                # empty file
                chat_ship = {}
                chat_ship[update.effective_chat.id] = {}
                for chat_member in chat_administrators:
                    chat_ship[update.effective_chat.id][chat_member.user.id] = 0
                json.dump(chat_ship, counters_fp)


def start(update: Update, context: CallbackContext):

    setup_shippering_file(update, context)

    text = '😄 Hello! SHIPPERING is a bot that will choose a couple of the day in your chat.\n\n ' \
           'Use /help for more info.'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def help(update: Update, context: CallbackContext):
    text = '💕 SHIPPERING is a bot that will choose a couple of the day in your chat. ' \
           'Everyone who writes a message in your chat will be added to the list of candidates' \
           'for a couple of the day. Add this bot to your chat' \
           'and wait for it to gather enough candidates before sending shipping command.' \
           '/help: this message'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def shipping(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        try:
            counters = json.load(counters_fp)

            ship1, ship2 = tuple(random.sample(range(0, len(counters[str(update.effective_chat.id)].keys())), k=2))

            user_id_shipped1 = list(counters[str(update.effective_chat.id)].items())[ship1][0]
            user_id_shipped2 = list(counters[str(update.effective_chat.id)].items())[ship2][0]
            counters[str(update.effective_chat.id)][user_id_shipped1] += 1
            counters[str(update.effective_chat.id)][user_id_shipped2] += 1

            logging.info(str(counters))
            with open('counters.json', 'w') as _counters_fp:
                json.dump(counters, _counters_fp)

            text = 'La coppia del giorno:' \
                f'{context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped1)} + {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped2)} = ❤️' \
                f'La nuova coppia del giorno potrà essere scelta tra 24 ore'

            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        except json.JSONDecodeError as e:
            logging.error("UNABLE TO READ FILE")
            context.bot.send_message(chat_id=update.effective_chat.id, text='Oops, something went wrong 😅')


def main():

    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    ship_handler = CommandHandler('shipping', shipping)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(ship_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()