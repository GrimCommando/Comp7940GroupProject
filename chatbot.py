## chatbot.py
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler,  CallbackQueryHandler, MessageHandler, Filters, CallbackContext

import os
# The messageHandler is used for all message updates
import configparser
import logging

import psycopg2
global postgres


#DB connection
def get_db_connection():
    config = configparser.ConfigParser()
    config.read('config.ini')
    conn = psycopg2.connect(host=config['POSTGRES']['HOST'],database=config['POSTGRES']['DATABASE'],user=config['POSTGRES']['USERNAME'],password=config['POSTGRES']['PASSWORD'])
    return conn
    
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
    
    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    # register a dispatcher to handle message: here we register an echo dispatcher
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("AddRoute", AddRoute))
    dispatcher.add_handler(CommandHandler("ListRoute", ListRoute))
    #dispatcher.add_handler(CommandHandler("AddReview", AddReview))
    #dispatcher.add_handler(CommandHandler("ListReview", ListReview))
    #dispatcher.add_handler(CommandHandler("ShareVideo", ShareVideo))
    dispatcher.add_handler(CommandHandler("ListVideo", ListVideo))
    
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # hello command
    dispatcher.add_handler(CommandHandler("hello", hello_command))
    
    #image handler
    dispatcher.add_handler(MessageHandler(Filters.photo, image_handler))
    
    #Video Handler    
    dispatcher.add_handler(MessageHandler(Filters.video, video_handler))
        
    dispatcher.add_handler(CommandHandler("start", start_command))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # To start the bot:
    updater.start_polling()
    logging.info("=== Bot running! ===")
    updater.idle()
    logging.info("=== Bot shutting down! ===")

def start_command(update, context):

    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    
    name = update.message.from_user.username
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
    
def video_handler(update,context):
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))    
    uname = str(update.message.from_user.username)    
    
    #download file
    file_name, file_extension = os.path.splitext(update.message.video.file_name)    
    file = update.message.video.file_id
    obj = context.bot.get_file(file)
    obj.download("Videos/" + update.message.video.file_unique_id + file_extension)
            
    try:
        postgres = get_db_connection()
        cur = postgres.cursor()      
        
        #print(update.message.video.file_unique_id)
        cur.execute("SELECT * FROM public.chatbot WHERE video_id=%s", (update.message.video.file_unique_id,))
        row = cur.fetchone()              
        
        if row == None:
            cur = postgres.cursor()
            print("There are no results for this query")
            postgres_insert_query = """ INSERT INTO public.chatbot (userid, video_id, username, caption,ext) VALUES (%s, %s, %s, %s, %s)"""
            record_to_insert = (update.message.message_id, update.message.video.file_unique_id, uname, update.message.caption,file_extension)
            cur.execute(postgres_insert_query,record_to_insert)
            postgres.commit() 
            row_count = cur.rowcount
            print(row_count, "Records Inserted")           
        
        else:
            cur = postgres.cursor()
            print("There are results for this query")
            postgres_update_query = """UPDATE public.chatbot SET userid = %s, username = %s, caption = %s  WHERE video_id = %s"""
            postgres_insert_query = """ INSERT INTO public.chatbot (userid, video_id, username, caption) VALUES (%s, %s, %s, %s)"""
            record_to_update = (update.message.message_id, uname, update.message.caption, update.message.video.file_unique_id)
            cur.execute(postgres_update_query,record_to_update)
            postgres.commit() 
            row_count = cur.rowcount
            print(row_count, "Records Updated")

    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into chatbot table", error)

    finally:    
        if postgres:
            cur.close()
            postgres.close()
            print("PostgreSQL connection is closed")
 
    update.message.reply_text("Video received")

def image_handler(update, context):
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))    
       
    update.message.reply_text("Image received")
    uname = str(update.message.from_user.username)   
    
    try:
        postgres = get_db_connection()
        cur = postgres.cursor()               
        
        cur.execute("SELECT * FROM public.chatbot WHERE photo_id=%s", (update.message.photo[-1].file_unique_id,))
        row = cur.fetchone()
        
        if row == None:
            print("There are no results for this query")
            file = update.message.photo[-1].file_id
            obj = context.bot.get_file(file)    
            file_name, file_extension = os.path.splitext(obj.file_path)
            obj.download("Images/" + update.message.photo[-1].file_unique_id + file_extension)
            
            postgres_insert_query = """ INSERT INTO public.chatbot (userid, photo_id, username, caption, ext) VALUES (%s, %s, %s, %s, %s)"""
            record_to_insert = (update.message.message_id, update.message.photo[-1].file_unique_id, uname, update.message.caption,file_extension)
            cur.execute(postgres_insert_query,record_to_insert)
            postgres.commit() 
            row_count = cur.rowcount
            print(row_count, "Records Inserted")
    
        else:
            print("There are results for this query")
            postgres_update_query = """UPDATE public.chatbot SET userid = %s, username = %s, caption = %s  WHERE photo_id = %s"""
            #postgres_insert_query = """ INSERT INTO public.chatbot (userid, photo_id, username, caption) VALUES (%s, %s, %s, %s)"""
            record_to_update = (update.message.message_id, uname, update.message.caption, update.message.photo[-1].file_unique_id)
            cur.execute(postgres_update_query,record_to_update)
            postgres.commit() 
            row_count = cur.rowcount
            print(row_count, "Records Updated")
        
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert record into chatbot table", error)

    finally:    
        if postgres:
            cur.close()
            postgres.close()
            print("PostgreSQL connection is closed")

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

def ListRoute(update, context):
    """Send a message when the command /add is issued."""
    try: 
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        
        try:
            postgres = get_db_connection()
            cur = postgres.cursor()               
            cur.execute("SELECT * FROM public.chatbot WHERE photo_id<>''")
            rows = cur.fetchall()
            
            for row in rows:
                print(row)                
                path="Images/"+row[2]+row[6]
                context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(path, 'rb'), caption=row[1])

        except (Exception, psycopg2.Error) as error:
            print("Failed to insert record into chatbot table", error)

        finally:    
            if postgres:
                cur.close()
                postgres.close()
                print("PostgreSQL connection is closed")

        
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')        

def ListVideo(update, context):
    """Send a message when the command /add is issued."""
    try: 
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        
        try:
            postgres = get_db_connection()
            cur = postgres.cursor()               
            cur.execute("SELECT * FROM public.chatbot WHERE video_id<>''")
            rows = cur.fetchall()
            
            for row in rows:
                print(row)                
                path="Videos/"+row[3]+row[6]
                context.bot.sendVideo(chat_id=update.effective_chat.id, video=open(path, 'rb'), caption=row[1])

        except (Exception, psycopg2.Error) as error:
            print("Failed to insert record into chatbot table", error)

        finally:    
            if postgres:
                cur.close()
                postgres.close()
                print("PostgreSQL connection is closed")

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /ListVideo <keyword>')        


def AddRoute(update, context):
    """Send a message when the command /add is issued."""
    try: 
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        
        #global redis1
        #logging.info('redis ' + context.args[0])
        msg = context.args[0]   # /add keyword <-- this should store the keyword
        #redis1.incr(msg)
        #update.message.reply_text('You have said ' + msg +  ' for ' + redis1.get(msg).decode('UTF-8') + ' times.')

        #get_db_connection()
           
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')        

if __name__ == '__main__':
    main()