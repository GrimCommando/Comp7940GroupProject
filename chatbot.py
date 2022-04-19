## chatbot.py
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler,  CallbackQueryHandler, MessageHandler, Filters, CallbackContext

import os
# The messageHandler is used for all message updates
import configparser
import logging
# Redis Database 
import redis

global redis


def main():

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO
    )
    
    # Load your token and create an Updater for your Bot
    config = configparser.ConfigParser()
    config.read('config.ini')
    #updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
    updater = Updater(token=(config['TELEGRAM']['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher
    
    global redis1
    redis1 = redis.Redis(host=(config['REDIS']['HOST']), password=(config['REDIS']['PASSWORD']), port=(config['REDIS']['REDISPORT']))
    #redis1 = redis.Redis(host=(os.environ['HOST']), password=(os.environ['PASSWORD']), port=(os.environ['REDISPORT']))
    
    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # register a dispatcher to handle message: here we register an echo dispatcher
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    #dispatcher.add_handler(CommandHandler("AddRoute", AddRoute))
    #dispatcher.add_handler(CommandHandler("ListRoute", ListRoute))
    #dispatcher.add_handler(CommandHandler("AddReview", AddReview))
    #dispatcher.add_handler(CommandHandler("ListReview", ListReview))
    #dispatcher.add_handler(CommandHandler("ShareVideo", ShareVideo))
    #dispatcher.add_handler(CommandHandler("ListVideo", ListVideo))
    
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # hello command
    dispatcher.add_handler(CommandHandler("hello", hello_command))
    
    #image handler
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))
    
    dispatcher.add_handler(CommandHandler("start", start_command))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # To start the bot:
    updater.start_polling()
    logging.info("=== Bot running! ===")
    updater.idle()
    logging.info("=== Bot shutting down! ===")

def start_command(update, context):
    name = update.message.chat.first_name
    update.message.reply_text("Hello " + name)
    update.message.reply_text("Please share your image")
    
     #"""Sends a message with three inline buttons attached."""
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data='1'),
            InlineKeyboardButton("Option 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    
def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text=f"Selected option: {query.data}")
    
    
def image_handler(update, context):
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    
    file = update.message.photo[-1].file_id
    obj = context.bot.get_file(file)
    obj.download("Images/" + update.message.photo[-1].file_unique_id +".jpg")
    
    update.message.reply_text("Image received")

def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you.')

def hello_command(update, context):
    try:
        reply_message = ('Hello ' + update.message.text[6:] +  '!')
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        #update.message.reply_text('Hello ' + reply_message +  '!')
        context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)
    except:
        update.message.reply_text('Usage: /hello <keyword>')

def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try: 
        global redis1
        logging.info('redis ' + context.args[0])
        msg = context.args[0]   # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg +  ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

def addRoute(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try: 
        global redis1
        logging.info('add route ' + context.args[0])
        msg = context.args[0]   # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg +  ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /addRoute <keyword>')
        

if __name__ == '__main__':
    main()