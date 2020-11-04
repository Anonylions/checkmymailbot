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

chats=[] # for storing all active chat_id's

updater = Updater(
    token=TG_TOKEN,
    use_context=True
)

# Reply Keyboard for start and stop buttons
keyboard = [[KeyboardButton(text = "/start"), KeyboardButton(text = "/stop")]]
options = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def run_checking(update, context):

    """
    Check a number of incoming emails for every 10 seconds
    and notifies user about new messages if that number changed from last time

    Parameters
    ----------
    update : 
    context : 
    """

    # Welcome message
    context.bot.send_message(
        update.message.chat_id,
        parse_mode=ParseMode.HTML,
        text='Hi! I\'m Alex, your new email assistant. I\'ll notify you every time you get a new email.',
        reply_markup=options
    )

    last_number_msg = 0     # How many emails we got after last check
    cur_number_msg = 0      # How many emails we got now
    
    # Initiate connection to a mail server
    with imaplib.IMAP4_SSL(
                host='imap.yandex.ru',
                port=993
        ) as M:

        M.login(EMAIL_NAME, EMAIL_PW) # Authentification

        while True:

            # If we don't have any active chats, then break out of a function 
            if str(update.message.chat_id) not in chats:
                return

            # Get a current number of incoming messages
            cur_number_msg = int(*M.select(mailbox='INBOX', readonly=True)[1])

            # Works only one time, after start.
            # We get and show number of unseen messages.
            if not(last_number_msg):

                (_, messages) = M.search(None, '(UNSEEN)')
                unseen_number = len(messages[0].decode('utf-8').split())

                context.bot.send_message(
                    update.message.chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'✉️ Now you have <b>{unseen_number}</b> unseen messages.'
                )

                last_number_msg = cur_number_msg

            # If the number of incoming messages changed, 
            # then send a notification (message)
            if cur_number_msg > last_number_msg:

                context.bot.send_message(
                    update.message.chat_id,
                    parse_mode=ParseMode.HTML,
                    text=f'📩 New message!'
                )

                last_number_msg = cur_number_msg

            # We check mail every 10 seconds
            time.sleep(10)


def start(update, context):

    """
    Basic command. Works one time, after getting /start from user.

    Parameters
    ----------
    update : 
    context : 
    """

    # We start a new thread only if its id is not in active chats list
    if str(update.message.chat_id) not in chats:
        
        new_thread = threading.Thread(target=run_checking, args=(update, context))
        new_thread.start()

        chats.append(str(update.message.chat_id)) # Add chat_id to active chats list

    else:
        # Else we send a warning message
        context.bot.send_message(
            update.message.chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, don\'t mess with me, okay? I\'m already running.',
        )


def stop(update, context):
    
    """
    Stops thread and getting updates from a mail server.

    Parameters
    ----------
    update : 
    context : 
    """

    # It shouldn't work before the bot is running
    if chats == []:

        context.bot.send_message(
            update.message.chat_id,
            parse_mode=ParseMode.HTML,
            text=f'⛔️ Hey, you should run me first!',
        )
        return

    # Remove chat_id from active chats list
    chats.remove(str(update.message.chat_id))

    # And send a farewell message
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