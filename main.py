import imaplib
import time
import os, signal
import threading
import logging

from telegram.ext import Updater, CommandHandler
from telegram import ParseMode, ReplyKeyboardMarkup, KeyboardButton


EMAIL_NAME = os.environ.get('EMAIL_NAME')
EMAIL_PW = os.environ.get('EMAIL_PW')

TG_TOKEN = os.environ.get('TG_CHECKMYMAILBOT_TOKEN')

chats=[]

updater = Updater(
    token=TG_TOKEN,
    use_context=True
)

keyboard = [[KeyboardButton(text = "/start"), KeyboardButton(text = "/stop")]]
options = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def run_checking(update, context):

    context.bot.send_message(
        update.message.chat_id,
        parse_mode=ParseMode.HTML,
        text='Hi! I\'m Alex, your new email assistant. I\'ll notify you every time you get a new email.',
        reply_markup=options
    )

    last_number_msg = 0
    cur_number_msg = 0
            
    with imaplib.IMAP4_SSL(
                host='imap.yandex.ru',
                port=993
        ) as M:

        M.login(EMAIL_NAME, EMAIL_PW)

        while True:

            if str(update.message.chat_id) not in chats:
                return

            cur_number_msg = int(*M.select(mailbox='INBOX', readonly=True)[1])

            if not(last_number_msg):

                (_, messages) = M.search(None, '(UNSEEN)')
                unseen_number = len(messages[0].decode('utf-8').split())

                context.bot.send_message(
                    update.message.chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'✉️ Now you have <b>{unseen_number}</b> unseen messages.'
                )

                last_number_msg = cur_number_msg

            if cur_number_msg > last_number_msg:

                context.bot.send_message(
                    update.message.chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'📩 New message!'
                )

                last_number_msg = cur_number_msg

            time.sleep(10)


def start(update, context):

    if str(update.message.chat_id) not in chats:
        new_thread = threading.Thread(target=run_checking, args=(update, context))
        new_thread.start()
        chats.append(str(update.message.chat_id))
    else:
        context.bot.send_message(
            update.message.chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, don\'t mess with me, okay? I\'m already running.',
        )


def stop(update, context):
    
    if chats == []:

        context.bot.send_message(
            update.message.chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, you should run me first!',
        )
        return

    chats.remove(str(update.message.chat_id))

    context.bot.send_message(
        update.message.chat_id,
        parse_mode=ParseMode.HTML,
        text=f'I was glad to help you. Bye 👋',
    )

    print(f'{threading.get_ident()} -- bye...')


def main():

    dispatcher = updater.dispatcher

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    startHandler = CommandHandler('start', start)
    stopHandler = CommandHandler('stop', stop)

    dispatcher.add_handler(startHandler)
    dispatcher.add_handler(stopHandler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()