import os
from unittest import result
from numpy import integer
import telebot
from telebot import types
from telebot.types import BotCommand
import csv
import emoji
from pymongo import MongoClient
from qna import Question
import pickle
from better_profanity import profanity
import pandas as pd
import time
from nospam import UserTimer


# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 

# Bot Token
my_secret = os.environ["API_KEY3"]
bot = telebot.TeleBot(my_secret)

@bot.message_handler(commands=['trysplit'])
def trysplit(message):
  bot.send_message(chat_id = message.chat.id, text = "File Split *Successful*!", parse_mode = "Markdown")
  return

bot.infinity_polling()