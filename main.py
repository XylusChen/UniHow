import os
import telebot
from telebot.types import BotCommand
from pymongo import MongoClient
from better_profanity import profanity
import pandas as pd
import time
from game import startgame
from chatbot import livechat, chatloop, endchat, stopsearch, resetchat, reportchat
from gipanel import gipanel, about, ugprogrammes, chs, biz, computing, dentistry, cde, law, medicine, nursing, pharmacy, music, spprogrammes, ddp, dmp, cdp, sp, sep, noc, usp, utcp, rvrc, jd, ptp, mp, housing, halls, eusoff, kr, ke7, raffles, sheares, temasek, houses, lighthouse, pioneer, rc, capt, rc4, tembusu, residences, pgp, utr
from generalfunc import filterfunc, filterfunc2, no_back, no_end, clearDB, resettimer, update_catQCount
from ask import askQuestion
from answer import ansQuestion, ansID
from browse import browse
from feedback_report import feedback, report
from test import test_func, test_func_class, test_func_class_random, test_chat

#Channel ID for testing Qna

testchannelQN =  os.environ['question_channel']
testchannelAns = os.environ['answer_channel']

# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

# About 
bot.register_message_handler(about, commands = ['about'])

# Math Game (Easter Egg)
bot.register_message_handler(startgame, commands = ['bored'], pass_bot = True)

# GIPanel feature
bot.register_message_handler(gipanel, commands = ['gipanel'])
bot.register_message_handler(ugprogrammes, commands = ['ugprogrammes'])
bot.register_message_handler(chs, commands = ['chs'])
bot.register_message_handler(biz, commands = ['biz'])
bot.register_message_handler(computing, commands = ['computing'])
bot.register_message_handler(dentistry, commands = ['dentistry'])
bot.register_message_handler(cde, commands = ['cde'])
bot.register_message_handler(law, commands = ['law'])
bot.register_message_handler(medicine, commands = ['medicine'])
bot.register_message_handler(nursing, commands = ['nursing'])
bot.register_message_handler(pharmacy, commands = ['pharmacy'])
bot.register_message_handler(music, commands = ['music'])
bot.register_message_handler(spprogrammes, commands = ['spprogrammes'])
bot.register_message_handler(ddp, commands = ['ddp'])
bot.register_message_handler(dmp, commands = ['dmp'])
bot.register_message_handler(cdp, commands = ['cdp'])
bot.register_message_handler(sp, commands = ['sp'])
bot.register_message_handler(sep, commands = ['sep'])
bot.register_message_handler(noc, commands = ['noc'])
bot.register_message_handler(usp, commands = ['usp'])
bot.register_message_handler(utcp, commands = ['utcp'])
bot.register_message_handler(rvrc, commands = ['rvrc'])
bot.register_message_handler(jd, commands = ['jd'])
bot.register_message_handler(ptp, commands = ['ptp'])
bot.register_message_handler(mp, commands = ['mp'])
bot.register_message_handler(housing, commands = ['housing'])
bot.register_message_handler(halls, commands = ['halls'])
bot.register_message_handler(eusoff, commands = ['eusoff'])
bot.register_message_handler(kr, commands = ['kr'])
bot.register_message_handler(ke7, commands = ['ke7'])
bot.register_message_handler(raffles, commands = ['raffles'])
bot.register_message_handler(sheares, commands = ['sheares'])
bot.register_message_handler(temasek, commands = ['temasek'])
bot.register_message_handler(houses, commands = ['houses'])
bot.register_message_handler(lighthouse, commands = ['lighthouse'])
bot.register_message_handler(pioneer, commands = ['pioneer'])
bot.register_message_handler(rc, commands = ['rc'])
bot.register_message_handler(capt, commands = ['capt'])
bot.register_message_handler(rc4, commands = ['rc4'])
bot.register_message_handler(tembusu, commands = ['tembusu'])
bot.register_message_handler(residences, commands = ['residences'])
bot.register_message_handler(pgp, commands = ['pgp'])
bot.register_message_handler(utr, commands = ['utr'])
  
# Live Chat Feature
bot.register_message_handler(livechat, commands = ['livechat'])
bot.register_message_handler(chatloop, content_types = ['text'], func = filterfunc)
bot.register_message_handler(endchat, commands = ['endchat'])
bot.register_message_handler(stopsearch, commands = ['stopsearch'])
bot.register_message_handler(reportchat, commands = ['reportchat'], pass_bot= True)


# Backwards Navigation at Main Menu
bot.register_message_handler(no_end, regexp = "End", func = filterfunc2)
bot.register_message_handler(no_back, regexp = "back", func = filterfunc2)

# Admin Commands
bot.register_message_handler(clearDB, commands = ['clearDB'])
bot.register_message_handler(resettimer, commands = ['resettimer'])
bot.register_message_handler(resetchat, commands = ['clearchat'])

# Test Commands
bot.register_message_handler(test_func, commands = ['test'])
bot.register_message_handler(test_func_class, commands = ['testclass'])
bot.register_message_handler(test_func_class_random, commands = ['testclassrandom'])
bot.register_message_handler(test_chat, commands = ['testchat'])

#Adding more censored words to the blacklist 
csv_black_list = pd.read_csv('blacklist.csv')
column_to_read_from_csv = csv_black_list.words 
list_of_additional_words_to_blacklist = list(column_to_read_from_csv)
profanity.add_censor_words(list_of_additional_words_to_blacklist)

#Set the commands in the main menu
bot.set_my_commands([
  BotCommand('start', 'Begin your UniHow journey!'),
  BotCommand('gipanel', 'Click here to learn all about NUS programs and accommodation options!'),
  BotCommand('askquestion', 'Send us your questions!'),
  BotCommand('unanswered', 'View unanswered questions in our QnA Forum!'),
  BotCommand('ansid', "Answer specific Questions using it's question ID!"),
  BotCommand('browse', 'Browse and search for relevant Questions Sets using QID or Keywords!'),
  BotCommand('livechat', 'Join our Chat Room!'),
  BotCommand('stopsearch', 'Stop searching for a chat!'),
  BotCommand('reportchat', 'Report current user you are chatting with.'),
  BotCommand('endchat', 'Leave the chat!'),
  BotCommand('about', 'Find out more about UniHow!'),
  BotCommand('feedback', 'Help us improve! Send us your feedback!'),
  BotCommand('reportqna', 'File a report! Help keep the UniHow community safe!')
])


# QnA Forum: Asking Questions
bot.register_message_handler(askQuestion, commands = ['askquestion'], pass_bot = True)

# QnA Forum: Answering Questions
bot.register_message_handler(ansQuestion, commands = ['unanswered'], pass_bot = True)
bot.register_message_handler(ansID, commands = ['ansid'], pass_bot = True)

# QnA Forum: Browsing Questions
bot.register_message_handler(browse, commands = ['browse'], pass_bot = True)

# Feedback
bot.register_message_handler(feedback, commands = ['feedback'], pass_bot = True)

# Report QnA Forum
bot.register_message_handler(report, commands = ['reportqna'], pass_bot = True)

    
#Define start command in main menu 
@bot.message_handler(commands=['start'])
def start(message):
  """Welcome new User!"""
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to UniHow! \n\n/gipanel to learn more about programs and accomodation options within NUS ! \n\n/askquestion if you want to ask a question! \n\n/unanswered to check out available questions to answer! \n\n/ansid to answer a question using its unique Question ID! \n\n/browse to browse and search for Question Sets! \n\n/livechat to engage in a real-time conversation with a University senior or Professor!"
  bot.reply_to(message, messageReply)

  bot.send_message(chat_id = message.chat.id, text = "We urge all users to behave responsibly on UniHow, especially when using our QnA Forum and LiveChat features. It takes a communal effort to keep this platform *safe* and *professional* so that everyone can use it with a peace of mind. If you notice any signs of misconduct or inappropriacy, please let us know by using our /report function, more detailed instructions will follow.", parse_mode = "Markdown")

  bot.send_message(chat_id= message.chat.id, text = "Make sure to subscribe to our [UniHow Question Channel](https://t.me/UniHowQuestion) to stay updated on the latest, most pressing questions that fellow peers are asking about NUS! Also subscribe to our [UniHow Answer Channel](https://t.me/UniHowAnswer) where you can find answers and responses to these questions!", parse_mode= 'Markdown')

update_catQCount()

if __name__ == '__main__': 
    try:
      bot.polling(none_stop=True)
      
    except Exception as e:
       print(e) 
       time.sleep(15)

