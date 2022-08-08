import os
import telebot
from telebot import types
from pymongo import MongoClient
import pickle
from generalfunc import code_to_cat_dict, go_back, userEnd, too_short, containsProfanity, go_back_message, short_warning, profanity_warning, broadcast_dic, five_posts, five_posts_announcement, not_number, not_number_text

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

# Defining the Edit command 
@bot.message_handler(commands=['edit'])
def edit(message, bot):
  username = message.from_user.first_name
  first = f"Hi {username}! Welcome to *UniHow QNA*! \n\nTo begin, please send us the *Question ID* of the pertaining question set that you wish to make an edit to. \n\nDo note that you are only allowed to edit your own submissions. You will not be able to edit Question or Answer contributions made by other users."
  current = bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'Markdown')
  bot.register_next_step_handler(current, editQID, bot)

def editQID(message, bot):
  """Check validity of user's QID input"""
  
  if go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you wish to make another edit!")
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you wish to make another edit!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, editQID, bot)
    return

  if not_number(message.text): 
    current = bot.send_message(chat_id = message.chat.id, text = not_number_text)
    bot.register_next_step_handler(current, editQID, bot)
    return

  # Search for Question Sets through database. 
  # Matching question ID, Unanswered.
  QID = int(message.text)
  results_count = collection.count_documents({"_id": QID})
  
  # If there are no available questions
  if results_count == 0:
    reply = "Oops! There is no existing question tagged with this number right now. Please try again with a valid number. If you do not wish to make an edit anymore, please type *end*."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'Markdown')
    bot.register_next_step_handler(current, editQID, bot)
    return

  result = collection.find_one({"_id": QID})
  question = result["question"]
  reply = f"This is your selected Question Set: \n\n{question} \n\nSelect if you wish to edit the Question or Answer."
  markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
  itembtn1 = types.KeyboardButton('Question')
  itembtn2 = types.KeyboardButton('Answer')
  markup.add(itembtn1, itembtn2)
  
  current = bot.send_message(chat_id = message.chat.id, text = reply, reply_markup = markup, parse_mode= 'Markdown')
  bot.register_next_step_handler(current, filterEdit, bot, result)


def filterEdit(message, bot, result):

  if go_back(message):
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, parse_mode = "Markdown")
    bot.register_next_step_handler(current, editQID, bot)
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you wish to make another edit!")
    return

  if containsProfanity(message):
    markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
    itembtn1 = types.KeyboardButton('Question')
    itembtn2 = types.KeyboardButton('Answer')
    markup.add(itembtn1, itembtn2)
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterEdit, bot, result)
    return    

  if message.text == "Question":

    userID = message.from_user.id
    from_user_id = result["from_user"]

    qns = pickle.loads(result["instance"])
    
    if userID != from_user_id:
      reply = "You are not allowed to edit this Question as it was not contributed by you. Please select another Question by sending it's QID. If you wish to leave the editing portal, send *end*"
      current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "Markdown")
      bot.register_next_step_handler(current, editQID, bot)
      return

    reply = "You may edit this Question as it was contributed by you. Please send us your updated Question after this message."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptEditQuestion, bot, qns, result)
    return

  if message.text == "Answer":
    stringID = str(message.from_user.id)
    qns = pickle.loads(result["instance"])
    answer_collection = qns.get_answerx5collection()
    
    if stringID not in answer_collection.keys():
      reply = "You are not allowed to edit any answers for this Question Set as you have not made an Answer contribution. Please select another Question by sending it's QID. \n\nTo answer a Question, use the /unanswered or /ansid commands. If you wish to leave the editing portal, send *end*."
      current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "Markdown")
      bot.register_next_step_handler(current, editQID, bot)
      return  

    original_answer = answer_collection[stringID]
    reply = f"This is your contributed answer: \n\n{original_answer} \n\nPlease send us your updated Answer after this message."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptEditAnswer, bot, qns, result)
    return   
    
  markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
  itembtn1 = types.KeyboardButton('Question')
  itembtn2 = types.KeyboardButton('Answer')
  markup.add(itembtn1, itembtn2)
  reply = "Your input is invalid. Please make your selection again."
  current = bot.send_message(chat_id = message.chat.id, text = reply, reply_markup = markup, parse_mode = "Markdown")
  bot.register_next_step_handler(current, filterEdit, bot, result)
  return

def acceptEditQuestion(message, bot, qns, result):
  
  if go_back(message):
    markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
    itembtn1 = types.KeyboardButton('Question')
    itembtn2 = types.KeyboardButton('Answer')
    markup.add(itembtn1, itembtn2)
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterEdit, bot, result)
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you wish to make another edit!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptEditQuestion, bot, qns)
    return    

  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptEditQuestion, bot, qns)
    return 

  updated_question = message.text
  qns.update_question(updated_question)
  pickled_qns = pickle.dumps(qns)
  # Update post/document in database.
  collection.update_one({"_id": result["_id"]}, {"$set": {"instance": pickled_qns, "question": updated_question}})
  reply = "Your Question has been successfully updated. Thank you for using our editing portal!"

  id = result["_id"]
  broadcast_message = f"*Category*: {code_to_cat_dict[qns.get_category()]}\n\n" + f"*Question* #*{id}*:\n{qns.get_question()}\n\n" + f"This question was updated. To answer this question, go to the [UniHow Bot](https://t.me/unihow_bot) and send \n */ansid*. Following that, simply send *{id}*."
  bot.send_message(chat_id = testchannelQN, text = broadcast_message, parse_mode= 'Markdown')  

  bot.send_message(chat_id= message.chat.id, text = reply, parse_mode = "Markdown")
  return

  
def acceptEditAnswer(message, bot, qns, result):
  if go_back(message):
    markup = types.ReplyKeyboardMarkup(row_width = 2, one_time_keyboard = True, resize_keyboard = True)
    itembtn1 = types.KeyboardButton('Question')
    itembtn2 = types.KeyboardButton('Answer')
    markup.add(itembtn1, itembtn2)
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterEdit, bot, result)
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you wish to make another edit!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, reply_markup = markup, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptEditAnswer, bot, qns)
    return    

  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptEditAnswer, bot, qns)
    return 

  stringID = str(message.from_user.id)
  updated_answer = message.text
  qns.answer_x5collection[stringID] = updated_answer
  pickled_qns = pickle.dumps(qns)
  # Update post/document in database.
  collection.update_one({"_id": result["_id"]}, {"$set": {"instance": pickled_qns, "answer_x5collection": qns.get_answerx5collection()}})
  reply = "Your Answer has been successfully updated. Thank you for using our editing portal!"

  # Post completed QS Set to Broadcast Channel
  id = result["_id"]
  broadcast_message = f"*Category*: {code_to_cat_dict[qns.get_category()]}\n\n" + f"*Question* #*{id}*:\n{qns.get_question()}\n\n" + f"*Answer*:\n{qns.get_answer(message.from_user.id)}" + "\n\nThis Answer was updated."
  bot.send_message(chat_id = testchannelAns, text = broadcast_message, parse_mode= "Markdown")
  broadcast_dic["count"] += 1

  if five_posts(broadcast_dic) : 
    bot.send_message(chat_id = testchannelAns, text = five_posts_announcement, parse_mode= "Markdown")

  bot.send_message(chat_id= message.chat.id, text = reply, parse_mode = "Markdown")
  return    