import os
import telebot
from telebot import types
from pymongo import MongoClient
import pickle
from generalfunc import code_to_cat_dict, createCatMarkup, sendCategoryList, go_back, userEnd, validCategory, containsProfanity, go_back_message, profanity_warning, containKeyword, user_cat_dic, not_number, not_number_text
from answer import accept_question_number

#Channel ID for testing (QnA)
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

# Defining the Browse command
@bot.message_handler(commands=['browse'])
def browse(message, bot):
  """Viewing Portal"""
  username = message.from_user.first_name
  first = f"Hi {username}! Welcome to *UniHow QnA Browsing Portal*! \n\nOur browsing portal allows you to conduct targeted searches for specific Question Sets using its unique Question ID or via Category and keywords. To begin, please select your preferred search and filter method. \n\nIf you wish to leave the browsing portal, please send *end*."
  
  markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
  itembtn1 = types.KeyboardButton('Question ID')
  itembtn2 = types.KeyboardButton('Category & Keywords')
  markup.add(itembtn1, itembtn2)
  
  current = bot.send_message(chat_id = message.chat.id, text = first, reply_markup = markup, parse_mode= 'Markdown')
  
  bot.register_next_step_handler(current, filterSearchMethod, bot)

# Processing user's Search Method choice. 
def filterSearchMethod(message, bot):
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our Browsing Portal! Come back anytime to browse for more Question Sets!")
    return  

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterSearchMethod, bot)
    return  

  if message.text == "Question ID":
    current = bot.send_message(chat_id = message.chat.id, text = "You have selected *Question ID*. \n\nTo continue, please send us the Question ID of the question set you wish to view. For example, if I want to view Question Set tagged #7, I will send *7*. Send the number now to view the Question Set. \n\nIf you wish to change your searching method, please send *back*.", parse_mode = "Markdown")
    bot.register_next_step_handler(current, searchByQID, bot)
    return

  if message.text == "Category & Keywords":
    bot.send_message(chat_id = message.chat.id, text = "You have selected *Category & Keywords*.", parse_mode = "Markdown")
    sendCategoryList(message)
    messageReply = "To continue, please send us the Category code of the question set you wish to view. \n\nIf you wish to change your searching method, please send *back*."
    markup = createCatMarkup()
    current = bot.send_message(chat_id = message.chat.id, text = messageReply, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, searchByCatKey, bot)    
    return

  # If User Input is invalid. 
  markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
  itembtn1 = types.KeyboardButton('Question ID')
  itembtn2 = types.KeyboardButton('Category & Keywords')
  markup.add(itembtn1, itembtn2)
  current = bot.send_message(chat_id = message.chat.id, text = "Your input was invalid. The only two acceptable search methods are by *Question ID* or *Category & Keywords*. Please check your input again. \n\nIf you wish to exit the browsing portal, please type *end*.", parse_mode= 'Markdown', reply_markup = markup)
  bot.register_next_step_handler(current, filterSearchMethod, bot)
  return

# Processing user's QID input.
def searchByQID(message, bot):
  if go_back(message):
    markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
    itembtn1 = types.KeyboardButton('Question ID')
    itembtn2 = types.KeyboardButton('Category & Keywords')
    markup.add(itembtn1, itembtn2)
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, parse_mode= "Markdown", reply_markup = markup)
    bot.register_next_step_handler(current, filterSearchMethod, bot)
    return

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA Browsing Portal! Come back anytime if you want to view more Question Sets!")
    return

  if message.text == "/ansid":
    current = bot.send_message(chat_id = message.chat.id, text = "You have been redirected to our answering portal! Please send the Question ID.")
    bot.register_next_step_handler(current, accept_question_number, bot)
    return
  
  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, searchByQID, bot)
    return   

  if not_number(message.text): 
    current = bot.send_message(chat_id = message.chat.id, text = not_number_text)
    bot.register_next_step_handler(current, searchByQID, bot)
    return 

  # Search for Question Sets through database. 
  # Matching question ID, Unanswered.
  QID = int(message.text)
  results_count = collection.count_documents({"_id": QID})
  
  # If there are no available questions
  if results_count == 0:
      reply = "Oops! There is no active question tagged with this number right now. Please try again with a valid number. If you wish to leave the Browsing Portal, please type *end*."
      current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'Markdown')
      bot.register_next_step_handler(current, searchByQID, bot)
      return
  
  result = collection.find_one({"_id": QID})
  qns = pickle.loads(result["instance"])
  # Send Question to user, along with Question ID.
  category = result["category"]
  question = result["question"]
  message1 = "*The question you have selected is:* \n\n" + f"*Category*: {code_to_cat_dict[category]}\n\n" + f"*Question #{QID}*:\n{question}"
  bot.send_message(chat_id = message.chat.id, text = message1, parse_mode= 'Markdown')

  if qns.get_answercount() == 0:
    message2 = "This question does not have any responses yet."
    bot.send_message(chat_id = message.chat.id, text = message2)

  if qns.get_answercount() > 0:
    message2 = "Here are the responses to this question:"
    bot.send_message(chat_id = message.chat.id, text = message2)
    for user in qns.get_answerx5collection().keys():
      bot.send_message(chat_id = message.chat.id, text = qns.get_answer(user))
  
  message3 = f"If you wish to contribute a response to the above question, use our /ansid command. Following which, send {QID} (Question ID). \n\nTo go back and and view a different question set, just send *back*. To leave the browsing portal, send *end*. \n\nDo not that Question Sets that have accumulated more than 5 responses are no longer available for new response contributions." 
  current = bot.send_message(chat_id = message.chat.id, text = message3, parse_mode= "Markdown")
  bot.register_next_step_handler(current, searchByQID, bot)
  return
      

# Processing user's Category Input
def searchByCatKey(message, bot):
  """Check validity of user's Category input"""
  if go_back(message):
    markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
    itembtn1 = types.KeyboardButton('Question ID')
    itembtn2 = types.KeyboardButton('Category & Keywords')
    markup.add(itembtn1, itembtn2)
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, parse_mode= "Markdown", reply_markup = markup)
    bot.register_next_step_handler(current, filterSearchMethod, bot)
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA Browsing Portal! Come back anytime if you want view more Question Sets!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, searchByCatKey, bot)
    return
  
  category = message.text
  user_cat_dic[message.from_user.id] = category
  # If User input is Valid. 
  if validCategory(message):
    reply = f"You have selected *{code_to_cat_dict[category]}*. \n\nTo continue, please send us the keyword(s) that you wish to further narrow your search by. If you intend to filter your results with more than one keyword, please leave a space between each keyword. \n\nFor example, if I wish to input the keyword *coding*, I will send 'coding'. If I wish to input the keywords *workload* and *module*, I will send 'workload module'. \n\nIf you do not wish to input any keywords, please send 'NA'.\n\nTo choose a new category, send *back*. To leave the browsing portal, send *end*."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "Markdown")
    bot.register_next_step_handler(current, keywordInput, bot)
    return

  else:
    reply = "Your input is invalid\. Please respond with a valid Category Code\. Note that the codes are *case sensitive* and you *should not* include the quotation marks\. \n\nIf you wish to leave our Browsing Portal, please type 'end' after this message\."
    markup = createCatMarkup()
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2', reply_markup = markup)
    bot.register_next_step_handler(current, searchByCatKey, bot)
    return

# Processing user's keyword(s) input
def keywordInput(message, bot):
  if go_back(message):
    markup = createCatMarkup()
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, parse_mode = "Markdown", reply_markup = markup)
    bot.register_next_step_handler(current, searchByCatKey, bot)
    return

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA Browsing Portal! Come back anytime if you want to view more Question Sets!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, searchByQID, bot)
    return  
  
  category = user_cat_dic[message.from_user.id]
  results_count = collection.count_documents({"category": category})
  if results_count == 0:
    markup = createCatMarkup()
    current = bot.send_message(chat_id = message.chat.id, text = "Oops! There are currently no Question Sets under your specified Category, please search with a new category.", reply_markup = markup)
    bot.register_next_step_handler(current, searchByCatKey, bot)
    return

  results = collection.find({"category": category})
  
  if message.text == "NA":
    for result in results:
      qID = result["_id"]
      id_text = f"*#{qID}*"
      q_string = result["question"]
      final = f"{q_string}\n\n{id_text}"
      bot.send_message(chat_id = message.chat.id, text = final, parse_mode = "Markdown")
    current = bot.send_message(chat_id = message.chat.id, text = "To view the responses to the above question(s), please send the corresponding Question ID")
    bot.register_next_step_handler(current, searchByQID, bot)
    return

  keywordList = message.text.split()
  count = 0
  for result in results:
    if containKeyword(keywordList, result):
      count += 1 
      qID = result["_id"]
      id_text = f"*#{qID}*"
      q_string = result["question"]
      final = f"{q_string}\n\n{id_text}"
      bot.send_message(chat_id = message.chat.id, text = final, parse_mode = "Markdown")

  if count == 0:
    current = bot.send_message(chat_id = message.chat.id, text = "Oops! There are current no Question Sets that contain the keywords you have keyed in, please try again with a different set of keywords!")
    bot.register_next_step_handler(current, keywordInput, bot)

  else:
    current = bot.send_message(chat_id = message.chat.id, text = "To view the responses to the above question(s), please send the corresponding Question ID.")
    bot.register_next_step_handler(current, searchByQID, bot)
    return    