import logging
import os
import json
import math
import random
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
from telegram import Update
from dotenv import load_dotenv
from datetime import time, datetime, timedelta

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

token = os.getenv('TELEGRAM_TOKEN')

chat_id = ''
deadline = datetime(datetime.today().year, datetime.today().month, datetime.today().day, hour=17)


def setup_shippering_file(update: Update, context: CallbackContext):
    if update.effective_chat.type != 'private':
        global chat_id
        chat_id = str(update.effective_chat.id)
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
                chat_ship[update.effective_chat.id]['shippable'] = True
                chat_ship[update.effective_chat.id]['user_counters'] = {}
                for chat_member in chat_administrators:
                    chat_ship[update.effective_chat.id]['user_counters'][chat_member.user.id] = 0
                chat_ship[update.effective_chat.id]['last_couple'] = []
                json.dump(chat_ship, counters_fp)


def start(update: Update, context: CallbackContext):

    setup_shippering_file(update, context)

    text = '😄 Hello! SHIPPERANG is a bot that will choose a couple of the day in your chat.\n\n ' \
           'Use /help for more info.'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def help(update: Update, context: CallbackContext):
    text = '💕 SHIPPERANG is a bot that will choose a couple of the day in your chat. ' \
           'Everyone who writes a message in your chat will be added to the list of candidates ' \
           'for a couple of the day. Add this bot to your chat ' \
           'and wait for it to gather enough candidates before sending shipping command.\n' \
           '/help: this message\n' \
           '/shipping: picks a couple of the day\n' \
           '/top: ship ranking\n' \
           '/last: last couples picked\n' \
           '/reset: delete every couple'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')


def shipping(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        try:
            counters = json.load(counters_fp)

        except json.JSONDecodeError as e:
            logging.error("UNABLE TO READ FILE")
            context.bot.send_message(chat_id=update.effective_chat.id, text='Oops, something went wrong 😅', parse_mode='HTML')
        logging.info(counters[str(update.effective_chat.id)]['last_couple'])
        if counters[str(update.effective_chat.id)]['shippable']:
            # last key is not counted for randomization since it's the last ship
            ship1, ship2 = tuple(
                random.sample(range(0, len(counters[str(update.effective_chat.id)]['user_counters'].keys())), k=2))

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

            counters[str(update.effective_chat.id)]['shippable'] = False
            # write updates
            with open('counters.json', 'w') as _counters_fp:
                json.dump(counters, _counters_fp)


        else:
            # if the ship for today is picked, only need to pop from the stack
            user_id_shipped2 = counters[str(update.effective_chat.id)]['last_couple'].pop()
            user_id_shipped1 = counters[str(update.effective_chat.id)]['last_couple'].pop()
        logging.info(counters[str(update.effective_chat.id)]['last_couple'])


        # find out how much needs to be waited to ship again
        now = datetime.today()
        time_to_wait = deadline - now
        total_seconds = time_to_wait.seconds + math.floor(round(time_to_wait.microseconds / 1000000, 1))
        hours, remaining_seconds = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remaining_seconds, 60)

        first_name1 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                  user_id=user_id_shipped1).user.first_name
        last_name1 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                 user_id=user_id_shipped1).user.last_name
        first_name2 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                  user_id=user_id_shipped2).user.first_name
        last_name2 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                 user_id=user_id_shipped2).user.last_name
        text = 'La coppia del giorno:\n\n' if counters[str(update.effective_chat.id)]['shippable'] else 'La coppia del giorno è già stata scelta:\n\n'
        text += f'<a href="tg://user?id={user_id_shipped1}">{first_name1} {last_name1}</a> ' if last_name1 else f'<a href="tg://user?id={user_id_shipped1}">{first_name1}</a>'
        text += f'+ <a href="tg://user?id={user_id_shipped2}">{first_name2} {last_name2}</a> = ❤\n' if last_name2 else f'+ <a href="tg://user?id={user_id_shipped2}">{first_name2}</a> = ❤\n'
        text += f'La nuova coppia del giorno potrà essere scelta tra {hours} ore, {minutes} minuti e {seconds} secondi'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')


def last_ship(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        text = 'Le coppie scelte negli ultimi giorni:\n\n'
        counters = json.load(counters_fp)
        last_couple_stack = counters[str(update.effective_chat.id)]['last_couple']
        for i in range(0, len(counters[str(update.effective_chat.id)]['last_couple']), 2):
            user_id_shipped2 = last_couple_stack.pop()
            user_id_shipped1 = last_couple_stack.pop()
            first_name1 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                      user_id=user_id_shipped1).user.first_name
            last_name1 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                     user_id=user_id_shipped1).user.last_name
            first_name2 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                      user_id=user_id_shipped2).user.first_name
            last_name2 = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                     user_id=user_id_shipped2).user.last_name
            text += '❤ = '
            text += f'{first_name1} {last_name1} + ' if last_name1 else f'{first_name1} + '
            text += f'{first_name2} {last_name2}\n' if last_name2 else f'{first_name2}\n'

        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')


def top_ship(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        text = 'Top lovers (coloro scelti il maggior numero di volte):\n\n'
        counters = json.load(counters_fp)
        id_items = list(counters[str(update.effective_chat.id)]['user_counters'].items())
        ranking = sorted(id_items, key=lambda id_counter : id_counter[1], reverse=True)
        i = 1
        for rank in ranking:
            logging.info(rank)
            logging.info(type(rank))
            first_name = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                      user_id=rank[0]).user.first_name
            last_name = context.bot.get_chat_member(chat_id=update.effective_chat.id,
                                                     user_id=rank[0]).user.last_name
            text += f'{i}. '
            text += f'{first_name} {last_name} — <b>{rank[1]}</b>\n' if last_name else f'{first_name} — <b>{rank[1]}</b>\n'
            i += 1
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='HTML')


def reset(update: Update, context: CallbackContext):
    setup_shippering_file(update, context)
    with open('counters.json') as counters_fp:
        counters = json.load(counters_fp)
        for user_id in counters[str(update.effective_chat.id)]['user_counters']:
            counters[str(update.effective_chat.id)]['user_counters'][user_id] = 0

        with open('counters.json', 'w') as _counters_fp:
            json.dump(counters, _counters_fp)

    context.bot.send_message(chat_id=update.effective_chat.id, text='Reset completato', parse_mode='HTML')


def callback_shipping():
    global deadline
    deadline += timedelta(days=1)
    with open('counters.json', 'r') as counters_fp:
        try:
            global chat_id
            counters = json.load(counters_fp)
            counters[chat_id]['shippable'] = True
            with open('counters.json', 'w') as _counters_fp:
                json.dump(counters, _counters_fp)
        except json.JSONDecodeError as e:
            logging.error("Couldn't open file")



def main():

    updater = Updater(token=token, use_context=True)

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    ship_handler = CommandHandler('shipping', shipping)
    last_ship_handler = CommandHandler('last', last_ship)
    top_ship_handler = CommandHandler('top', top_ship)
    reset_handler = CommandHandler('reset', reset)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(ship_handler)
    dispatcher.add_handler(last_ship_handler)
    dispatcher.add_handler(top_ship_handler)
    dispatcher.add_handler(reset_handler)

    shipping_job = updater.job_queue
    shipping_job.run_daily(callback_shipping, deadline.time())

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()