import os
import telebot
from telebot import types
import csv
import emoji
from pymongo import MongoClient
from better_profanity import profanity
from qna import Question
import pandas as pd
from chatbot import collection_match, relationship_dic


# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

# Filter function for chatloop
whitelist = ['end', 'back']

def filterfunc(message):
  if message.text.lower() in whitelist:
    return False
  if not message.entities:
    return True
  for entity in message.entities:
    if entity.type == "bot_command":
      return False
  return True

def filterfunc2(message):
  if not message.entities:
    return True
  for entity in message.entities:
    if entity.type == "bot_command":
      return False
  return True

# List of all valid categories for QnA feature 
validCats = ["chs", "biz", "computing", "medicine", "dentistry", "cde", "law", "nursing", "pharmacy", "music", "UGgeneral", "ddp", "dmp", "cdp", "sep", "noc", "usp", "utcp", "jd", "ptp", "mp", "SPgeneral", "eusoff", "kr", "ke7", "raffles", "sheares", "temasek", "lighthouse", "pioneer", "rvrc", "capt", "rc4", "tembusu",  "pgp", "utr", "Hgeneral"]

#To post the full category name instead of just the code itself. 
code_to_cat_dict = {'chs': "College of Humanities and Sciences 📕",  'biz' : "NUS Business School 💼", 'computing' : "School of Computing 💻" , 'medicine': "Yong Loo Lin School of Medicine 🩺" , 'dentistry': "Faculty of Dentistry 🦷", 'cde': "College of Design and Engineering 🎨🔧", 'law': "Faculty of Law 🏛️", 'nursing' :"Alice Lee Centre for Nursing Studies & Yong Loo Lin School of Medicine 💉", 'pharmacy':  "Department of Pharmacy 💊", 'music' : "Yong Siew Toh Conservatory of Music 🎵", 'UGgeneral' : "General Enquires for Undegraduate Programmes ☀️", 'ddp' : "Double Degree Programmes 🗞️🗞️", 'dmp': "Double Major Programmes 📜📜", 'cdp' : "Concurrent Degree Programmes 🗞️♾️🗞️", 'sep': "Student Exchange Programme 💱" ,'noc' : "NUS Overseas Colleges ✈️" ,'usp' : "University Scholars Programme 👨‍🎓" ,'utcp' :"University Town College Programme 🏫", 'rvrc' :  "Ridge View Residential College 🏘️", 'jd' : "Joint Degree Programmes 🏫🗞️🏫", 'ptp' : "Part Time Programmes 🗞️🕣", 'mp' : "Minor Programmes 📜", 'SPgeneral' : "General Enquiries for Special Undergraduate Programmes ☀️", 'eusoff' : "Eusoff Hall 🏡", 'kr' : "Kent Ridge Hall 🏡", 'ke7' : "King Edward VII Hall 🏡", 'raffles' : "Raffles Hall 🏡", 'sheares' : "Sheares Hall 🏡", 'temasek' : "Temasek Hall 🏡", 'lighthouse' : "LightHouse 🏠", 'pioneer' : "Pioneer House 🏠", 'rvrc' : "Ridge View Residential College 🏘️", 'capt' : "College of Alice & Peter Tan Residential College 🏘️", 'rc4' : "Residential College 4 🏘️", 'tembusu' : "Tembusu College 🏘️", 'pgp' : "PGP Residence 🏢", 'utr' : "UTown Residence 🏢", 'Hgeneral':  "General Enquiries for NUS Housing ☀️"}

# Create Keyboard MarkUp for Category selection
def createCatMarkup():
  markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True)
  for cat in validCats:
    itembtn = types.KeyboardButton(cat)
    markup.add(itembtn)
  return markup

#In case user tries to end when there is no activity in  progress. 
@bot.message_handler(regexp = "End", func = filterfunc2)
def no_end(message):
  if len(message.text) > 3:
    return
  bot.send_message(chat_id = message.chat.id, text = "You are already at the main menu. Please use the menu to select what you want to do.")

#In case user tries to go back when there is no activity in progress. 
@bot.message_handler(regexp = "back", func = filterfunc2)
def no_back(message):
  if len(message.text) > 4:
    return
  bot.send_message(chat_id = message.chat.id, text = "You are already at the main menu. Please use the menu to select what you want to do. " )

#Read csv file
def read_csv(csvfilename):
  """
  Reads a csv file and returns a list of lists
  containing rows in the csv file and its entries.
  """
  with open(csvfilename, encoding='utf-8') as csvfile:
      rows = [row for row in csv.reader(csvfile)]
  return rows

# Sends out lists of Valid Categories
def sendCategoryList(message):
  ug = emoji.emojize("*Categories for Undergraduate Programmes* \n\n 'chs' College of Humanities and Sciences :closed_book:\n\n 'biz' NUS Business School :briefcase:\n\n 'computing' School of Computing :laptop:\n\n 'medicine' Yong Loo Lin School of Medicine :stethoscope:\n\n 'dentistry' Faculty of Dentistry :tooth:\n\n 'cde' College of Design and Engineering :artist_palette::wrench:\n\n 'law' Faculty of Law :classical_building:\n\n 'nursing' Alice Lee Centre for Nursing Studies & Yong Loo Lin School of Medicine :syringe:\n\n 'pharmacy' Department of Pharmacy :pill:\n\n 'music' Yong Siew Toh Conservatory of Music :musical_note:\n\n 'UGgeneral' General Enquires for Undegraduate Programmes :sun:") 
  bot.send_message(chat_id = message.chat.id, text = ug, parse_mode = 'MarkdownV2')
  sp = emoji.emojize("*Categories for Special Undergraduate Programmes* \n\n 'ddp' Double Degree Programmes :rolled-up_newspaper::rolled-up_newspaper:\n\n 'dmp' Double Major Programmes :scroll::scroll:\n\n 'cdp' Concurrent Degree Programmes :rolled-up_newspaper::infinity::rolled-up_newspaper:\n\n 'sep' Student Exchange Programme :currency_exchange:\n\n 'noc' NUS Overseas Colleges :airplane:\n\n 'usp' University Scholars Programme :man_student:\n\n 'utcp' University Town College Programme :school:\n\n 'rvrc' Ridge View Residential College :houses:\n\n 'jd' Joint Degree Programmes :school::rolled-up_newspaper::school:\n\n 'ptp' Part Time Programmes :rolled-up_newspaper::eight-thirty:\n\n 'mp' Minor Programmes :scroll:\n\n 'SPgeneral' General Enquiries for Special Undergraduate Programmes :sun:") 
  bot.send_message(chat_id = message.chat.id, text = sp, parse_mode = 'MarkdownV2')
  housing = emoji.emojize("*Categories for NUS Housing and Accomodation* \n\n 'eusoff' Eusoff Hall :house_with_garden:\n\n 'kr' Kent Ridge Hall :house_with_garden:\n\n 'ke7' King Edward VII Hall :house_with_garden:\n\n 'raffles' Raffles Hall :house_with_garden:\n\n 'sheares' Sheares Hall :house_with_garden:\n\n 'temasek' Temasek Hall :house_with_garden:\n\n 'lighthouse' LightHouse :house:\n\n 'pioneer' Pioneer House :house:\n\n 'rvrc' Ridge View Residential College :houses:\n\n 'capt' College of Alice & Peter Tan Residential College :houses:\n\n 'rc4' Residential College 4 :houses:\n\n 'tembusu' Tembusu College :houses:\n\n 'pgp' PGP Residence :office_building:\n\n 'utr' UTown Residence :office_building:\n\n 'Hgeneral' General Enquiries for NUS Housing :sun:")
  bot.send_message(chat_id = message.chat.id, text = housing, parse_mode = 'MarkdownV2')
  return

def go_back(message) :
  if message.text.lower() == "back":
    return True 
  else: 
    return False 
go_back_message = "You have requested to go back. Please make your selection again."

# Check if user wishes to terminate QnA Session
def userEnd(message):
  if message.text.lower() == "end":
    return True
  else:
    return False

# Check if question or answer is too short to avoid misuse of bot. 20 characters minimum. 
def too_short(message):
  len_string = len(message.text)
  if len_string < 20 : 
    return True
  else :
    return False 
short_warning = "Your input is too short. We hope to create an environment where our users will ask questions, provide answers or feedback that are constructive and will be of value to everyone. Thank you for understanding! Please key in your input again."
    
# Check if user input is a valid Category
def validCategory(message):
  userInput = message.text
  if userInput in validCats:
    return True
  else:
    return False

# Python dictionary, stores user_id as keys and QS instances as value.
category_dic = {}
# Fetch question instance from category_dic
def fetch_question(message):
  user = message.from_user.id
  qns = category_dic[user]
  return qns

# Check if message is a reply. 
# If true, returns the original message that was replied to, else returns False. 
def isReply(message):
  if message.reply_to_message:
    return message.reply_to_message
  return False

# Detect Profanity in User Input.
# Adding more censored words to the blacklist 
csv_black_list = pd.read_csv('blacklist.csv')
column_to_read_from_csv = csv_black_list.words 
list_of_additional_words_to_blacklist = list(column_to_read_from_csv)
profanity.add_censor_words(list_of_additional_words_to_blacklist)

def containsProfanity(message):
  if profanity.contains_profanity(message.text):
    return True
  return False
profanity_warning = "Your input contains inappropriate language. We hope to create a safe and positive environment at UniHow that empowers our users to learn more about NUS so as to better shape their university life. Thank you for understanding! Please key in your input again.\n\n*Warning*\nWe seek your cooperation in keeping our UniHow platform a safe and professional one. Inappropriate use of language can be flagged by community members and may result in a permanent ban."

# Finds the largest existing qID in database. 
# Purpose of this function will be explained in acceptQuestion() function.
def findLargestID():
  results = collection.find({})
  max = 0
  for result in results:
    if result["_id"] > max:
      max = result["_id"]
  return max

# Python dictionary, user_id as key, UserTimer instance as value.
timeTrack = {}

# Python Dictionary, Key: Category, Value: No. of Unanswered Questions.
catQCount = {}

def update_catQCount():
  # Reset. All Question count set to 0.
  for cat in validCats:
    catQCount[cat] = 0
  catQCount["updated"] = False

  # Search for existing unanswered Questions in database.
  results_count = collection.count_documents({"status": False})
  results = collection.find({"status": False})

  # Database empty.
  if results_count == 0:
    catQCount["updated"] = True
    return

  # Update Question count for respective categories.
  for result in results:
    cat = result["category"]
    catQCount[cat] += 1
  catQCount["updated"] = True
  return

# Periodic broadcast announcement for the bot, every 5 Question posts. Counter starts at 0. 
broadcast_dic= {"count" : 0 }
  
# Admin commands, please DO NOT execute when testing our bot. Thanks!
xylus = int(os.environ['Xylus_ID'])
jay = int(os.environ['Jay_ID'])
admin = [xylus, jay]

#admin command
def resetchat(message): 
	if message.chat.id in admin:
		collection_match.delete_many({})
		relationship_dic.clear()
		bot.send_message(chat_id= message.chat.id, text= " Reset MongoDB chatbot! Relationship dictionary cleared!", parse_mode= "Markdown")


def clearDB(message):
  """Clear Database"""
  if message.from_user.id not in admin:
    bot.send_message(chat_id = message.chat.id, text = "You do not have access to this command!")
    return
  
  collection.delete_many({})
  update_catQCount()
  Question.id_counter = 0
  broadcast_dic["count"] = 0
  messageReply = "Database Cleared! catQCount reset! id_counter reset! broadcast_count reset! "
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['resettimer'])
def resettimer(message):
  if message.from_user.id not in admin:
    bot.send_message(chat_id = message.chat.id, text = "You do not have access to this command!")
    return
    
  timeTrack.clear()
  bot.send_message(chat_id = message.chat.id, text = "Timer Reset!")
  return

def containKeyword(keywordList, result):
  for keyword in keywordList:
    if keyword not in result["question"]:
      return False
  return True

user_cat_dic = {}

#checks if bot needs to broadcast an announcement. 
def five_posts(dic) :
    if dic["count"] >= 5 :
      dic["count"] = 0 
      return True 
five_posts_announcement = "Dear users, thank you for using UniHow. We hope that our QnA feature has brought value to you. If you notice any offensive or inappropriate posts, you may report it and the admins will be glad to take a look. It is easy to do so. Simply go to the [UniHow bot](https://t.me/unihow_bot) and send */reportqna*."

#checks if user responds with a number
def not_number(s):
    try:
        float(s)
        return False
    except ValueError:
        return True
not_number_text = "Your input was not a number. Please try again! "