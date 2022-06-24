import os
from unittest import result
import telebot
from telebot.types import BotCommand
import csv
import emoji
import pymongo
from pymongo import MongoClient
from qna import Question
import pickle
from better_profanity import profanity
import pandas as pd
import time
from nospam import UserTimer
import threading

#MongoDB databse for QnA feature 
cluster = MongoClient("mongodb+srv://unihow:unihow@cluster0.ed1i7.mongodb.net/?retryWrites=true&w=majority")
db = cluster["telegram"]
collection = db["unihow"] 

my_secret = os.environ["API_KEY3"]
bot = telebot.TeleBot(my_secret)

# List of all valid categories for QnA feature 
validCats = ["chs", "biz", "computing", "medicine", "dentistry", "cde", "law", "nursing", "pharmacy", "music", "UGgeneral", "ddp", "dmp", "cdp", "sp", "jd", "ptp", "mp", "SPgeneral", "eusoff", "kr", "ke7", "raffles", "sheares", "temasek", "lighthouse", "pioneer", "rvrc", "capt", "rc4", "tembusu", "Hgeneral", "sep", "noc", "usp", "utcp", "pgp", "utr"]

active_cats = []
def getActiveCats():
  threading.Timer(3, getActiveCats).start()
  results = collection.find({"status": False})
  for result in results:
    if result["category"] not in active_cats:
      active_cats.append(result["category"])

getActiveCats()
      
# Python dictionary to store user-category data pair. User unique ID (key), Category chosen (value)
category_dic = {}

#Read csv file
def read_csv(csvfilename):
  """
  Reads a csv file and returns a list of lists
  containing rows in the csv file and its entries.
  """
  with open(csvfilename, encoding='utf-8') as csvfile:
      rows = [row for row in csv.reader(csvfile)]
  return rows

#adding more censored words 
csv_black_list = pd.read_csv('blacklist.csv')
saved_column = csv_black_list.words #you can also use df['column_name']
list_words = list(saved_column)
print(list_words)
profanity.add_censor_words(list_words)



#Set the commands in the main menu
bot.set_my_commands([
  BotCommand('start', 'Begin your UniHow journey!'),
  BotCommand('gipanel', 'Click here to learn all about NUS programs and accommodation options!'),
  BotCommand('askquestion', 'Send us your questions!'),
  BotCommand('ansquestion', 'Assist peers with their queries!'),
  BotCommand('livechat', 'Join our Chat Room!'),
  BotCommand('about', 'Find out more about UniHow!')
])

# Sends out list of Valid Categories
def sendCategoryList(message):
  ug = emoji.emojize("*Categories for Undergraduate Programmes* \n\n 'chs' College of Humanities and Sciences :closed_book:\n\n 'biz' NUS Business School :briefcase:\n\n 'computing' School of Computing :laptop:\n\n 'medicine' Yong Loo Lin School of Medicine :stethoscope:\n\n 'dentistry' Faculty of Dentistry :tooth:\n\n 'cde' College of Design and Engineering :artist_palette::wrench:\n\n 'law' Faculty of Law :classical_building:\n\n 'nursing' Alice Lee Centre for Nursing Studies & Yong Loo Lin School of Medicine :syringe:\n\n 'pharmacy' Department of Pharmacy :pill:\n\n 'music' Yong Siew Toh Conservatory of Music :musical_note:\n\n 'UGgeneral' General Enquires for Undegraduate Programmes :sun:") 
  bot.send_message(chat_id = message.chat.id, text = ug, parse_mode = 'MarkdownV2')
  sp = emoji.emojize("*Categories for Special Undergraduate Programmes* \n\n 'ddp' Double Degree Programmes :rolled-up_newspaper::rolled-up_newspaper:\n\n 'dmp' Double Major Programmes :scroll::scroll:\n\n 'cdp' Concurrent Degree Programmes :rolled-up_newspaper::infinity::rolled-up_newspaper:\n\n 'sep' Student Exchange Programme :currency_exchange:\n\n 'noc' NUS Overseas Colleges :airplane:\n\n 'usp' University Scholars Programme :man_student:\n\n 'utcp' University Town College Programme :school:\n\n 'rvrc' Ridge View Residential College :houses:\n\n 'jd' Joint Degree Programmes :school::rolled-up_newspaper::school:\n\n 'ptp' Part Time Programmes :rolled-up_newspaper::eight-thirty:\n\n 'mp' Minor Programmes :scroll:\n\n 'SPgeneral' General Enquiries for Special Undergraduate Programmes :sun:") 
  bot.send_message(chat_id = message.chat.id, text = sp, parse_mode = 'MarkdownV2')
  housing = emoji.emojize("*Categories for NUS Housing and Accomodation* \n\n 'eusoff' Eusoff Hall :house_with_garden:\n\n 'kr' Kent Ridge Hall :house_with_garden:\n\n 'ke7' King Edward VII Hall :house_with_garden:\n\n 'raffles' Raffles Hall :house_with_garden:\n\n 'sheares' Sheares Hall :house_with_garden:\n\n 'temasek' Temasek Hall :house_with_garden:\n\n 'lighthouse' LightHouse :house:\n\n 'pioneer' Pioneer House :house:\n\n 'rvrc' Ridge View Residential College :houses:\n\n 'capt' College of Alice & Peter Tan Residential College :houses:\n\n 'rc4' Residential College 4 :houses:\n\n 'tembusu' Tembusu College :houses:\n\n 'pgp' PGP Residence :office_building:\n\n 'utr' UTown Residence :office_building:\n\n 'Hgeneral' General Enquiries for NUS Housing :sun:")
  bot.send_message(chat_id = message.chat.id, text = housing, parse_mode = 'MarkdownV2')
  return

# Check if user wishes to terminate QnA Session
def userEnd(message):
  endList = ["end", 'end', "END", "'END'", "/end", "/END", 'End']
  if message.text in endList:
    return True
  else:
    return False

#Check if question or answer is too short to avoid misuse of bot. 20 characters minimum. 
def too_short(message):
  len_string = len(message.text)
  if len_string < 20 : 
    return True
  else :
    return False 
    
# Check if user input is valid: user input should not contain Bot Command
def validInput(message):
  entities = message.entities
  if entities:
    for entity in entities:
      if entity.type == "bot_command":
        return False
  else:
    return True

# Check if user input is a valid Category
def validCategory(message):
  userInput = message.text
  if userInput in validCats:
    return True
  else:
    return False

# Fetch question instance from category_dic
def fetch_question(message):
  user = message.from_user.id
  qns = category_dic[user]
  return qns

# Check if message is a reply. 
def isReply(message):
  if message.reply_to_message:
    return message.reply_to_message
  return False
  
#Defining the Ask Question command 
@bot.message_handler(commands=['askquestion'])
def askQuestion(message):
  username = message.from_user.first_name
  first = f"Hi {username}\! Welcome to *UniHow QnA*\!"

  bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'MarkdownV2')
  
  sendCategoryList(message)
  

  last = "To ask a question, all you have to do is send the category code pertaining to the subject your question is about. For example, If I wish to ask a question about the College of Humanities and Sciences, I will just type *chs*. If you wish to end this session, just reply with *end*."

  current = bot.send_message(chat_id = message.chat.id, text = last, parse_mode = 'Markdown')
  bot.register_next_step_handler(current, filterCategoryQuestion)


def filterCategoryQuestion(message):
  """Check validity of user's Category input"""

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you have a question for us!")
    return

  if not validInput(message):
    current = bot.send_message(chat_id = message.chat.id, text = "Your Category Code should not contain any Bot Commands, please try again!\n\nIf you do not wish to submit a Question anymore, please type 'end' after this message.")
    bot.register_next_step_handler(current, filterCategoryQuestion)
    return

  category = message.text
  if validCategory(message):
    reply = f"You have selected *{message.text}*\. Please type your question after this message\."
    user = message.from_user.id
    category_dic[user] = Question(user, category)
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2')
    bot.register_next_step_handler(current, acceptQuestion)
  else:
    reply = "Your input is invalid\. Please respond with a valid Category Code\. Note that the codes are *case sensitive* and you *should not* include the quotation marks\. \n\nIf you do not wish to submit a Question anymore, please type 'end' after this message\."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2')
    bot.register_next_step_handler(current, filterCategoryQuestion)

def findLargestID():
  results = collection.find({})
  max = 0
  for result in results:
    if result["_id"] > max:
      max = result["_id"]
  return max

timeTrack = {}
id_counter = 0

def acceptQuestion(message):
  """Accepting a user's Question"""

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you have a question for us!")
    return

  user = message.from_user.id
  if user in timeTrack:
    timerInstance = timeTrack[user]
    status = timerInstance.canSend()
    if not status:
      timeLeft = timerInstance.timeTillSend()
      bot.send_message(chat_id = message.chat.id, text = f"You have recently just posted a Question! Users are allowed to post one question every *5 minutes*, this is to prevent unnecessary spamming and overloading of our servers. Thank you for your cooperation! \n\nYou may post your next question in *{timeLeft}* seconds.", parse_mode = "Markdown")
    return
    
  if profanity.contains_profanity(message.text):
    current = bot.send_message(chat_id = message.chat.id, text = "Your input contains inappropriate language. We hope to create a safe and positive environment at UniHow that empowers our users to learn more about NUS so as to better shape their university life. Thank you for understanding! Please key in your input again.\n\n*Warning*\nWe seek your cooperation in keeping our UniHow platform a safe and professional one. Inappropriate use of language can be flagged by community members and may result in a permanent ban.", parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptQuestion)
    return   

  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = "Your input is too short. We hope to create an environment where our users will ask questions and submit answers that will be of value to everyone. Thank you for understanding! Please key in your input again.")
    bot.register_next_step_handler(current, acceptQuestion)
    return 

  if not validInput(message):
    current = bot.send_message(chat_id = message.chat.id, text = "Your question should not contain any Bot Commands, please try again!\n\nIf you do not wish to submit a Question anymore, please type 'end' after this message.")
    bot.register_next_step_handler(current, acceptQuestion)
    return


  qns = fetch_question(message)
  qns.update_question(message.text)
  pickled_qns = pickle.dumps(qns) 
  
  try:
    post = {"_id": Question.id_counter, "status": qns.get_status(), "from_user": qns.get_from_user(), "category": qns.get_category(), "question": qns.get_question(), "instance": pickled_qns}
    collection.insert_one(post)
    Question.id_counter += 1
  
  except:
    largest = findLargestID()
    Question.id_counter = largest + 1
    post = {"_id": Question.id_counter, "status": qns.get_status(), "from_user": qns.get_from_user(), "category": qns.get_category(), "question": qns.get_question(), "instance": pickled_qns}
    collection.insert_one(post)
    Question.id_counter += 1

  finally:
    user = message.from_user.id
    timeTrack[user] = UserTimer(user, time.time())

    bot.send_message(chat_id = message.chat.id, text = "Thank you for your input, you question has been recorded! Do check out our UniHow QnA Broadcast Channel soon to see if someone has answered your question! [UniHow Qna Broadcast Channel](https://t.me/UniHowQnA)", parse_mode= 'Markdown')

  
#Telling user the current number of unanswered questions
def unanswered_ques(message):
  total_count = 0
  for cat in active_cats: 
    result_count = collection.count_documents({"status": False, "category": cat})
    if result_count > 0 :
      total_count = total_count + result_count
      bot.send_message(chat_id = message.chat.id, text = f"There are *{result_count}* unanswered questions in *{cat}*", parse_mode = 'Markdown')
  
  if total_count == 0 :
    bot.send_message(chat_id = message.chat.id, text = "There are *no* unanswered questions at the moment. Feel free to come back later! ", parse_mode = 'Markdown')
    return

  else : 
    last = bot.send_message(chat_id = message.chat.id, text = "The above are available categories with unanswered questions. Please reply with the category code to access them. \n\nFor example, if there are unanswered questions in 'medicine', I will respond with *medicine* to access the unanswered questions. To end, simply reply *end*.", parse_mode = 'Markdown')
    bot.register_next_step_handler(last, filterCategoryAnswer)
  



#Defining the Answer Question command 
@bot.message_handler(commands=['ansquestion'])
def ansQuestion(message):
  """Answer a Question! """
  username = message.from_user.first_name
  first = f"Hi {username}! Welcome to *UniHow QnA*! Below are all the available categories provided where other users can post questions under. You may then answer those questions."
  bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'Markdown')

  sendCategoryList(message)

  unanswered_ques(message)


def filterCategoryAnswer(message):
  """Check validity of user's Category input"""

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if not validInput(message):
    current = bot.send_message(chat_id = message.chat.id, text = "Your Category Code should not contain any Bot Commands, please try again!\n\nIf you do not wish to answer a Question anymore, please type 'end' after this message.")
    bot.register_next_step_handler(current, filterCategoryAnswer)
    return

  category = message.text
  if validCategory(message):
    reply = f"You have selected *{category}*\. Please wait while we search for questions under this Category\."
    bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "MarkdownV2")
    results_count = collection.count_documents({"status": False, "category": category})
    results = collection.find({"status": False, "category": category})
    
    # If there are no available questions
    if results_count == 0:
      reply = "Oops! There are no available questions of this category at the moment! Please try again later! \n\nIf you wish to select a new Category, please respond with the new Category code after this message. If you do not wish to answer a Question anymore, please type 'end'."
      current = bot.send_message(chat_id = message.chat.id, text = reply)
      bot.register_next_step_handler(current, filterCategoryAnswer)
      return
  
    for result in results:
      qID = result["_id"]
      id_text = f"*#{qID}*"
      q_string = result["question"]
      final = f"{q_string}\n\n{id_text}"
      bot.send_message(chat_id = message.chat.id, text = final, parse_mode = "Markdown")
    reply = "To answer a question, please reply the corresponding message with your answer using Telegram's reply function! Thank you!"
    current = bot.send_message(chat_id = message.chat.id, text = reply)
    bot.register_next_step_handler(current, acceptAnswer)
    
  else:
    reply = "Your input is invalid\. Please respond with a valid Category Code\. Note that the codes are *case sensitive* and you *should not* include the quotation marks\. \n\nIf you do not wish to answer a Question anymore, please type 'end' after this message\."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2')
    bot.register_next_step_handler(current, filterCategoryAnswer)


def acceptAnswer(message):
  """Accepting a user's Answer to existing Question"""
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if profanity.contains_profanity(message.text):
    current = bot.send_message(chat_id = message.chat.id, text = "Your input contains inappropriate language. We hope to create a safe and positive environment at UniHow that empowers our users to learn more about NUS so as to better shape their university life. Thank you for understanding! Please key in your input again.\n\n*Warning*\nWe seek your cooperation in keeping our UniHow platform a safe and professional one. Inappropriate use of language can be flagged by community members and may result in a permanent ban.", parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptAnswer)
    return   
  
  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = "Your input is too short. We hope to create an environment where our users will ask questions and submit answers that will be of value to everyone. Thank you for understanding! Please key in your input again.")
    bot.register_next_step_handler(current, acceptAnswer)
    return 
  
  if not validInput(message):
    current = bot.send_message(chat_id = message.chat.id, text = "Your Answer should not contain any Bot Commands, please try again!\n\nIf you do not wish to answer a Question anymore, please type 'end' after this message.")
    bot.register_next_step_handler(current, acceptAnswer)
    return

  if not isReply(message):
    current = bot.send_message(chat_id = message.chat.id, text = "We are unable to record your Answer as your input is not a *Reply* to one of our Questions\. Please make sure you are *replying to the message* corresponding to the question you are trying to answer\.", parse_mode = "MarkdownV2")
    bot.register_next_step_handler(current, acceptAnswer)
    return


  question_message = isReply(message)
  message_string = question_message.text
  full = message_string.split("\n")
  qID_string = full[-1][1:]
  qID_int = int(qID_string)
  result = collection.find_one({"_id": qID_int})
  qns = pickle.loads(result["instance"])
  qns.update_answer(message.from_user.id, message.text)
  collection.update_one({"_id": qID_int}, {"$set": {"status": qns.get_status(), "answered_by": qns.get_answered_by(), "answer": qns.get_answer()}})
  bot.send_message(chat_id = message.chat.id, text = emoji.emojize("Your Answer has been successfully recorded! We would like to thank you for your contribution on behalf of the UniHow community! :smiling_face_with_smiling_eyes:. To view your answer, check out[UniHow Qna Broadcast Channel](https://t.me/UniHowQnA)."), parse_mode= 'Markdown')

  broadcast_message = f"*Category*: {qns.category}\n\n" + f"*Question* #*{qID_int}*:\n{qns.question}\n\n" + f"*Answer*:\n{qns.answer}"
  bot.send_message(chat_id = -1001712487991, text = broadcast_message, parse_mode= "Markdown")

  
#Defining the livechat command 
@bot.message_handler(commands=['clearDB'])
def clearDB(message):
  """Clear Database"""
  collection.delete_many({})
  messageReply = "Database Cleared!"
  bot.reply_to(message, messageReply)

#Define start command in main menu 
@bot.message_handler(commands=['start'])
def start(message):
  """Welcome new User!"""
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to UniHow! \n\n/gipanel to learn more about programs and accomodation options within NUS ! \n\n/askquestion if you want to ask a question! \n\n/ansquestion if you want to answer a question! \n\n/livechat to engage in a real-time conversation with a University senior or Professor!"
  bot.reply_to(message, messageReply)

  bot.send_message(chat_id = message.chat.id, text = "We urge all users to behave responsibly on UniHow, especially when using our QnA Forum and LiveChat features. It takes a communal effort to keep this platform *safe* and *professional* so that everyone can use it with a peace of mind. If you notice any signs of misconduct or inappropriacy, please let us know by using our /report function, more detailed instructions will follow.", parse_mode = "Markdown")

  bot.send_message(chat_id= message.chat.id, text = "Make sure to subscribe to the [UniHow Qna Broadcast Channel](https://t.me/UniHowQnA) to gain access to our channel where you can find answers to the most pressing questions that our users are asking about NUS!", parse_mode= 'Markdown')

#Define gipanel command in main menu 
@bot.message_handler(commands=['gipanel'])
def gipanel(message):
  """Shows the user the menu for gi panel """
  messageReply = emoji.emojize(f"This is the menu for our general information panel. *Click on the links* below to find out various information about NUS Undergraduate Programmes, Special Undergraduate Programmes, as well as accomodation options available in NUS.\n\n /ugprogrammes Undergraduate Programmes :school: \n\n /spprogrammes Special Undergraduate Programmes :school::star: \n\n /housing Accomodation on Campus :house:")
  bot.reply_to(message, messageReply, parse_mode= 'Markdown')

  
#Defining the livechat command 
@bot.message_handler(commands=['livechat'])
def liveChat(message):
  """Enter Chat Room! """
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to the Chat Room!"
  bot.reply_to(message, messageReply)

#Defining the About command 
@bot.message_handler(commands=['about'])
def about(message):
  username = message.from_user.first_name
  filename = "aboutUniHow.csv"
  data = read_csv(filename)
  messageReply = f"Hi {username}! "
  messageReply += data[1][0]
  bot.send_message(chat_id=message.chat.id, text=emoji.emojize(messageReply))
  
#define Undergraduate Programmes menu 
@bot.message_handler(commands=['ugprogrammes'])
def ugprogrammes(message):
  """Undergraduate programmes/Faculties"""
  messageReply = emoji.emojize(f"Find out all about NUS Undergraduate Programmes here! *Click on the links* to discover more about NUS Faculties and the degree courses they offer! \n\n/chs College of Humanities and Sciences :closed_book::microscope:\n\n/biz NUS Business School :briefcase:\n\n/computing School of Computing :laptop:\n\n/medicine Yong Loo Lin School of Medicine 	:stethoscope:\n\n/dentistry Faculty of Dentistry :tooth:\n\n/cde College of Design and Engineering :artist_palette::wrench:\n\n/law Faculty of Law :classical_building:\n\n/nursing Alice Lee Centre for Nursing Studies & Yong Loo Lin School of Medicine :syringe:\n\n/pharmacy Department of Pharmacy :pill:\n\n/music Yong Siew Toh Conservatory of Music :musical_note:")
  bot.reply_to(message, messageReply, parse_mode= 'Markdown')

#Abstraction for the bot to reply based on "final" command 
def generateReply(input, filename, message):
  data = read_csv(filename)
  index = data[0].index(input)
  description = data[1][index]
  link = data[2][index]
  username = message.from_user.first_name
  greeting = emoji.emojize(f"Hi {username}! Welcome to {data[3][index]}! {data[4][index]} \n\n")
  text = f'Click [here]({link}) to find out more\!'
  bot.reply_to(message, greeting + description)
  bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')

  
#Defining all the commands within Undergraduate Programmes
@bot.message_handler(commands=['chs'])
def chs(message):
  """College of Humanities and Sciences"""
  generateReply('chs', 'faculties.csv', message)

@bot.message_handler(commands=['biz'])
def biz(message):
  """NUS School of Business"""
  generateReply('biz', 'faculties.csv', message)


@bot.message_handler(commands=['computing'])
def computing(message):
  """NUS School of Computing"""
  generateReply('computing', 'faculties.csv', message)


@bot.message_handler(commands=['dentistry'])
def dentistry(message):
  """NUS Faculty of Dentistry"""
  generateReply('dentistry', 'faculties.csv', message)

@bot.message_handler(commands=['cde'])
def cde(message):
  """NUS College of Design and Engineering"""
  generateReply('cde', 'faculties.csv', message)


@bot.message_handler(commands=['law'])
def law(message):
  """NUS Faculty of Law"""
  generateReply('law', 'faculties.csv', message)


@bot.message_handler(commands=['medicine'])
def medicine(message):
  """NUS Medicine"""
  generateReply('medicine', 'faculties.csv', message)


@bot.message_handler(commands=['nursing'])
def nursing(message):
  """NUS Nursing"""
  generateReply('nursing', 'faculties.csv', message)


@bot.message_handler(commands=['pharmacy'])
def pharmacy(message):
  """NUS Pharmacy"""
  generateReply('pharmacy', 'faculties.csv', message)


@bot.message_handler(commands=['music'])
def music(message):
  """NUS Music"""
  generateReply('music', 'faculties.csv', message)


  
#Define menu for Special Programmes 
@bot.message_handler(commands=['spprogrammes'])
def spprogrammes(message):
  """Special Undergraduate Programmes """
  messageReply = emoji.emojize(f"*Click on the links* below to find out various information about Special Undergraduate Programmes in NUS.\n\n/ddp Double Degree Programmes :rolled-up_newspaper::rolled-up_newspaper:\n\n/dmp Double Major Programmes :scroll::scroll:\n\n/cdp Concurrent Degree Programmes :rolled-up_newspaper::infinity::rolled-up_newspaper:\n\n/sp Special Programmes :star::rolled-up_newspaper:\n\n/jd Joint Degree Programmes :school::rolled-up_newspaper::school:\n\n/ptp Part Time Programmes :rolled-up_newspaper::eight-thirty:\n\n/mp Minor Programmes :scroll:")
  bot.reply_to(message, messageReply, parse_mode= 'Markdown')

#Defining all the individual commands inside Special Programmes 

@bot.message_handler(commands=['ddp'])
def ddp(message):
  """Double Degree Programmes"""
  generateReply('ddp', 'spp.csv', message)

@bot.message_handler(commands=['dmp'])
def dmp(message):
  """Double Major Programmes"""
  generateReply('dmp', 'spp.csv', message)

@bot.message_handler(commands=['cdp'])
def cdp(message):
  """Concurrent Degree Programmes """
  generateReply('cdp', 'spp.csv', message)

@bot.message_handler(commands=['sp'])
def sp(message):
  """Special Programmes """
  messageReply = emoji.emojize("Welcome to NUS Special Programmes! Here you can find out about unique and intriguing academic initiatives that are capable of making your University experience so much more enriching! *Click on the various links* below to find out more! \n\n/sep Student Exchange Programme :currency_exchange:\n\n/noc NUS Overseas Colleges :airplane:\n\n/usp University Scholars Programme :man_student:\n\n/utcp University Town College Programme :school:\n\n/rvrc Ridge View Residential College :houses:")
  bot.reply_to(message, messageReply, parse_mode= 'Markdown')

@bot.message_handler(commands=['sep'])
def sep(message):
  """Student Exchange Programme"""
  generateReply('sep', 'spp.csv', message)

@bot.message_handler(commands=['noc'])
def noc(message):
  """NUS Overseas Colleges"""
  generateReply('noc', 'spp.csv', message)

@bot.message_handler(commands=['usp'])
def usp(message):
  """University Scholars Programme"""
  generateReply('usp', 'spp.csv', message)

@bot.message_handler(commands=['utcp'])
def utcp(message):
  """University Town College Programme"""
  generateReply('utcp', 'spp.csv', message)

@bot.message_handler(commands=['rvrc'])
def rvrc(message):
  """Ridge View Residential College"""
  generateReply('rvrc', 'spp.csv', message)

@bot.message_handler(commands=['jd'])
def jd(message):
  """Joint Degree Programmes"""
  generateReply('jd', 'spp.csv', message)

@bot.message_handler(commands=['ptp'])
def ptp(message):
  """Part-time Programmes"""
  generateReply('ptp', 'spp.csv', message)

@bot.message_handler(commands=['mp'])
def mp(message):
  """Minor Programmes"""
  generateReply('mp', 'spp.csv', message)

#Defining the menu for accommodation
@bot.message_handler(commands=['housing'])
def housing(message):
  """Accomodation on Campus"""
  messageReply = emoji.emojize(
        f"Looking for an opportunity to stay in campus? Craving for the 'full' uni-experience? You've come to the right place! *Click on the links* below to find out more about on-campus living and accomodation options in NUS.\n\n/halls Halls :house_with_garden:\n\n/houses Houses :house:\n\n/rc Residential Colleges :houses:\n\n/residences Residences :office_building:"
    )
  bot.reply_to(message, messageReply, parse_mode= 'Markdown')
  text = 'Click [here](https://nus.edu.sg/osa/student-services/hostel-admission/undergraduate/application-guide) for more administrative information on NUS Hostel Admissions, such as Eligibility, Application Periods and Hostel Fees etc\!'
  bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')

#Defining the individual commands for accommodation (halls)
@bot.message_handler(commands=['halls']) 
def halls(message):
  """Hall"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Halls of Residences! \n\nExpect personal development opportunities through a myriad of co-curricular activities across sports, community engagement and cultural activities. Some General Education modules and Design-Your-Own-Module are offered here, with opportunities for elected student leadership via the Junior Common Room Committee (JCRC). Meal plans included. Here are NUS Hall options! \n\n/eusoff Eusoff Hall :eagle::blue_book:::white_flower: \n\n/kr Kent Ridge Hall :lion::books: \n\n/ke7 King Edward VII Hall :eagle:	:closed_book::lion: \n\n/raffles Raffles Hall :tiger::eagle: \n\n/sheares Sheares Hall :green_book::lion: \n\n/temasek Temasek Hall :lion::scroll:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['eusoff'])
def eusoff(message):
  """Eusoff Hall"""
  generateReply('eusoff', 'housing.csv', message)

@bot.message_handler(commands=['kr'])
def kr(message):
  """Kent Ridge Hall"""
  generateReply('kr', 'housing.csv', message)

@bot.message_handler(commands=['ke7'])
def ke7(message):
  """King Edward VII Hall"""
  generateReply('ke7', 'housing.csv', message)

@bot.message_handler(commands=['raffles'])
def raffles(message):
  """Raffles Hall"""
  generateReply('raffles', 'housing.csv', message)

@bot.message_handler(commands=['sheares'])
def sheares(message):
  """Sheares Hall"""
  generateReply('sheares', 'housing.csv', message)

@bot.message_handler(commands=['temasek'])
def temasek(message):
  """Temasek Hall"""
  generateReply('temasek', 'housing.csv', message)

#Defining the individual commands for accommodation (houses)
@bot.message_handler(commands=['houses'])
def houses(message):
  """House"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Houses! \n\nExpect lots of ground-up initiatives co-led by residents, peer mentorship, and a structured Proactive Pastoral Care (PPC) system – where every resident is assigned to a small yet robust support group. Collaborative student leadership roles are available as a Peer Mentor, Resident Assistant, or the Student Council. No meal plans. Currently there are two Houses. Explore them now! \n\n/lighthouse LightHouse :sun::house:\n\n/pioneer Pioneer House :palm_tree::lion:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['lighthouse'])
def lighthouse(message):
  """LightHouse"""
  generateReply('lighthouse', 'housing.csv', message)

@bot.message_handler(commands=['pioneer'])
def pioneer(message):
  """Pioneer House"""
  generateReply('pioneer', 'housing.csv', message)

#Defining the individual commands for accommodation (residential colleges)
@bot.message_handler(commands=['rc'])
def rc(message):
  """Residential Colleges"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Residential Colleges! \n\nExpect a diverse range of academic modules taught in intimate settings, dynamic and informal out-of-classroom learning, and student interest groups. Elected student leadership roles are available via the College Students’ Committee (CSC) and in interest groups. Meal plans included. Here are NUS Residential College Options! \n\n/rvrc Ridge View Residential College :four_leaf_clover: \n\n/capt College of Alice & Peter Tan :closed_book:::handshake::deciduous_tree:  \n\n/rc4 Residential College 4 :house::dolphin::light_bulb:\n\n/tembusu Tembusu College :evergreen_tree:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['capt'])
def capt(message):
  """College of Alice & Peter Tan"""
  generateReply('capt', 'housing.csv', message)

@bot.message_handler(commands=['rc4'])
def rc4(message):
  """Residential College 4"""
  generateReply('rc4', 'housing.csv', message)

@bot.message_handler(commands=['tembusu'])
def tembusu(message):
  """Tembusu College"""
  generateReply('tembusu', 'housing.csv', message)

#Defining the individual commands for accommodation (residences)
@bot.message_handler(commands=['residences'])
def residences(message):
  """Student Residences"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Student Residences! \n\nResidents here have the option to participate in residential activities at a level that they are comfortable with. Programmes across themes of wellness, personal effectiveness, sports, cultural appreciation and community service are offered. Student leadership roles are available via the Resident Assistant and Cluster Leader role.  No meal plans. For speedy updates on your mobile phone, go to the uNivUS app, select 'Resources' and then 'Residential Living'. Currently, there are two Student Residences. Discover them now! \n\n/pgp PGP Residence :leaf_fluttering_in_wind: \n\n/utr UTown Residence :house_with_garden:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['pgp'])
def pgp(message):
  """PGP Residence"""
  generateReply('pgp', 'housing.csv', message)

@bot.message_handler(commands=['utr'])
def utr(message):
  """UTown Residence"""
  generateReply('utr', 'housing.csv', message)


bot.infinity_polling()
