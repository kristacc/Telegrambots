#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Based on:
# Simple Bot to reply to Telegram messages and timed Telegram messages
# https://github.com/python-telegram-bot/python-telegram-bot
# This program is dedicated to the public domain under the CC0 license.



from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Job
import logging, time, random, StringIO
import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

# message saving
text={}



# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
	update.message.reply_text('Moips!')


def help(bot, update):
	update.message.reply_text('Help not done!')
	update.message.reply_text('/history prints ALL your messages \n' + '/random gives you a random memory \n')


def echo(bot, update):
	global text
	user = update.message.chat.id
	if user not in text:
		text[ user ] = []
	text[user].append( {"msg": update.message.text, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "t": time.time() })
	#update.message.reply_text(update.message.text)


def error(bot, update, error):
	logger.warn('Update "%s" caused error "%s"' % (update, error))


def alarm(bot, job):
	"""Function to send the alarm message"""
	bot.send_message(job.context, text='Beep!')


def set(bot, update, args, job_queue, chat_data):
	"""Adds a job to the queue"""
	chat_id = update.message.chat_id
	try:
		# args[0] should contain the time for the timer in seconds
		due = int(args[0])
		if due < 0:
			update.message.reply_text('Sorry we can not go back to future!')
			return

		# Add job to queue
		job = job_queue.run_once(alarm, due, context=chat_id)
		chat_data['job'] = job

		update.message.reply_text('Timer successfully set!')

	except (IndexError, ValueError):
		update.message.reply_text('Usage: /set <seconds>')


def unset(bot, update, chat_data):
	"""Removes the job if the user changed their mind"""

	if 'job' not in chat_data:
		update.message.reply_text('You have no active timer')
		return

	job = chat_data['job']
	job.schedule_removal()
	del chat_data['job']

	update.message.reply_text('Timer successfully unset!')



def backup(bot, update):
	out = ""
	user = update.message.chat.id
	if user not in text:
		text[ user ] = []
		
	for line in text[ user ]:
		out +=line["time"] + "    " + line["msg"] + "\r\n"
		
	#doc = telegram.InputFile( {"document": StringIO.StringIO( out ), "filename": "backup.txt"} )
	if len( out ) > 0:
		update.message.reply_text('Backuping...')
		bot.send_document( chat_id = update.message.chat.id, document = StringIO.StringIO( out ), filename = "backup.txt" )
	else:
		update.message.reply_text('Nothing to backup :/')

	
	
def randomm(bot, update):
	
	#out = random.choice( text )
	#update.message.reply_text( out["time"] + "    " + out["msg"] )
	user = update.message.chat.id
	if user not in text:
		text[ user ] = []
		
	if len( text[ user ] )  < 1:
		update.message.reply_text('No memories found :(')
		return
	
	update.message.reply_text('Random memory:')
	index = random.randint( 0, len(text[ user ]) -1 )
	print text[index]["msg"]
	
	i = index
	n_s = 0
	n_e = 0
	go_forward = True
	
	# go into older messages if previous message is less than 45min appart
	# to find the first diary marking of that "session" was that
	# annettu teksti - annettu teksti
	while (( index + n_s - 1 ) >= 0) and go_forward:
		if text[ user ][index + n_s]["t"] - text[ user ][i-1]["t"] < 45*60:
			n_s -= 1
			i -= 1
		else:
			go_forward = False
	
	# and last:
	i = index
	go_forward = True
	while (( index + n_e + 1 ) < len(text[ user ]) ) and go_forward:
		if text[ user ][index + n_e + 1]["t"] - text[ user ][i]["t"] < 45*60:
			n_e+=1
			i+=1
		else: 
			go_forward = False
	
	print n_s
	print n_e
	
	for i in range (( index + n_s ), ( index + n_e +1 )):
		update.message.reply_text( text[ user ][i]["time"] + "    " + text[ user ][i]["msg"] )
	

def history(bot, update):
	user = update.message.chat.id
	print user
	if user not in text:
		text[ user ] = []
		
	if len( text[ user ] ) > 0:
		update.message.reply_text('Your history:')
		out = ""
		for line in text[ user ]:
			out +=line["time"] + "    " + line["msg"] + "\n"
		
		update.message.reply_text(out)
		#update.message.reply_text('\n'.join( text ))
	else:
		update.message.reply_text('No history found.')
	
def erase(bot, update):
	global text
	user = update.message.chat.id
	if user not in text:
		text[ user ] = []
		
	#update.message.reply_text('Erasing your history...')
	text[ user ] = []
	update.message.reply_text('Erased your history.')

def main():
	# Create the EventHandler and pass it your bot's token. DearDiaryBot
	updater = Updater("TOKEN")

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# on different commands - answer in Telegram
	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", help))
	dp.add_handler(CommandHandler("set", set,
								  pass_args=True,
								  pass_job_queue=True,
								  pass_chat_data=True))
	dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))
	dp.add_handler(CommandHandler("backup", backup))
	dp.add_handler(CommandHandler("history", history))
	dp.add_handler(CommandHandler("random", randomm))
	dp.add_handler(CommandHandler("erase", erase))

	# on noncommand i.e message - echo the message on Telegram
	dp.add_handler(MessageHandler(Filters.text, echo))

	# log all errors
	dp.add_error_handler(error)

	# Start the Bot
	updater.start_polling()

	# Run the bot until you press Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	updater.idle()


if __name__ == '__main__':
	main()
