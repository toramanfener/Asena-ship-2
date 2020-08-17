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
                chat_ship[update.effective_chat.id]['user_counters'] = {}
                for chat_member in chat_administrators:
                    chat_ship[update.effective_chat.id]['user_counters'][chat_member.user.id] = 0
                chat_ship[update.effective_chat.id]['last_couple'] = []
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

            # last key is not counted for randomization since it's the last ship
            ship1, ship2 = tuple(random.sample(range(0, len(counters[str(update.effective_chat.id)]['user_counters'].keys())), k=2))

            # find the id whose index in the key list is the rng number
            user_id_shipped1 = list(counters[str(update.effective_chat.id)]['user_counters'].items())[ship1][0]
            user_id_shipped2 = list(counters[str(update.effective_chat.id)]['user_counters'].items())[ship2][0]

            counters[str(update.effective_chat.id)]['user_counters'][user_id_shipped1] += 1
            counters[str(update.effective_chat.id)]['user_counters'][user_id_shipped2] += 1
            counters[str(update.effective_chat.id)]['last_couple'].append(user_id_shipped1)
            counters[str(update.effective_chat.id)]['last_couple'].append(user_id_shipped2)
            if len(counters[str(update.effective_chat.id)]['last_couple']) > 10:
                counters[str(update.effective_chat.id)]['last_couple'].pop(0)
                counters[str(update.effective_chat.id)]['last_couple'].pop(0)

            # write updates
            with open('counters.json', 'w') as _counters_fp:
                json.dump(counters, _counters_fp)

            # text = 'La coppia del giorno:' \
            #     f'{context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped1)} + {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped2)} = ❤️' \
            #     f'La nuova coppia del giorno potrà essere scelta tra 24 ore'
            text='Yo'
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        except json.JSONDecodeError as e:
            logging.error("UNABLE TO READ FILE")
            context.bot.send_message(chat_id=update.effective_chat.id, text='Oops, something went wrong 😅')


def last_ship(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        text = 'Le coppie scelte negli ultimi giorni:\n'
        counters = json.load(counters_fp)
        last_couple_stack = counters[str(update.effective_chat.id)]['last_couple']
        for i in range(0, len(counters[str(update.effective_chat.id)]['last_couple']), 2):
            user_id_shipped1 = last_couple_stack.pop()
            user_id_shipped2 = last_couple_stack.pop()
            text += f'❤ = {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped1)} + {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=user_id_shipped2)}\n'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def top_ship(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        text = 'Top lovers (coloro scelti il maggior numero di volte).:\n'
        counters = json.load(counters_fp)
        id_items = list(counters[str(update.effective_chat.id)]['user_counters'].items())
        ranking = sorted(id_items, key=lambda id_counter : id_counter[1], reverse=True)
        logging.info(ranking)
        i = 1
        for rank in ranking:
            text += f'{i}. {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=rank[0])} — {context.bot.get_chat_member(chat_id=update.effective_chat.id, user_id=rank[1])}\n'
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def main():

    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    ship_handler = CommandHandler('shipping', shipping)
    last_ship_handler = CommandHandler('last', last_ship)
    top_ship_handler = CommandHandler('top', top_ship)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(ship_handler)
    dispatcher.add_handler(last_ship_handler)
    dispatcher.add_handler(top_ship_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()