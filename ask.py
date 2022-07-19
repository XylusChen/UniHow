import os
import telebot
from pymongo import MongoClient
from qna import Question
import pickle
import time
from nospam import UserTimer
from generalfunc import code_to_cat_dict, createCatMarkup, sendCategoryList, go_back, userEnd, too_short, validCategory, fetch_question, containsProfanity, go_back_message, short_warning, profanity_warning, category_dic, findLargestID, timeTrack, catQCount, update_catQCount

#Channel ID for testing (QnA)
testchannelQN =  -1001541561678
testchannelAns = -1001797479601

# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

# Defining the Ask Question command 
@bot.message_handler(commands=['askquestion'])
def askQuestion(message, bot):
  username = message.from_user.first_name
  first = f"Hi {username}\! Welcome to *UniHow QnA*\!"
  bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'MarkdownV2')
  
  sendCategoryList(message)
  
  last = "To ask a question, all you have to do is send the category code pertaining to the subject your question is about. \n\nFor example, If I wish to ask a question about the College of Humanities and Sciences, I will just type *chs*. If you wish to end this session, just reply with *end*. \n\nPlease note that you may submit 1 question every *3 minutes*."

  markup = createCatMarkup()
  
  current = bot.send_message(chat_id = message.chat.id, text = last, reply_markup = markup, parse_mode = 'Markdown')
  bot.register_next_step_handler(current, filterCategoryQuestion, bot)

# Process User's category selection.
def filterCategoryQuestion(message, bot):
  """Check validity of user's Category input"""

  if go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you have a question for us!")
    return
  
  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you have a question for us!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterCategoryQuestion, bot)
    return
  
  category = message.text
  # If User input is Valid.
  if validCategory(message):
    reply = f"You have selected *{message.text}*. Please type your question after this message. To go back and select a different category, just send *back*."
    user = message.from_user.id

    # Upon successful category selection, new QS instance is initialized. 
    # Stored as value in dictionary with User_ID as key.
    category_dic[user] = Question(user, category)
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'Markdown')
    bot.register_next_step_handler(current, acceptQuestion, bot)

  # If User input is Invalid.
  else:
    reply = "Your input is invalid\. Please respond with a valid Category Code\. Note that the codes are *case sensitive* and you *should not* include the quotation marks\. \n\nIf you do not wish to submit a Question anymore, please type 'end' after this message\."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2')
    bot.register_next_step_handler(current, filterCategoryQuestion, bot)


# Process User's Question input.
def acceptQuestion(message, bot):
  """Accepting a user's Question"""

  if go_back(message): 
    markup = createCatMarkup()
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, reply_markup = markup, parse_mode= "Markdown")
    bot.register_next_step_handler(current, filterCategoryQuestion, bot)
    return

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you have a question for us!")
    return

  # Creates UserTimer instance for User. 
  # UserTimer instance keeps track of time since User's latest Question post. 
  # 3min interval between question submissions, prevent spam.
  user = message.from_user.id
  if user in timeTrack:
    timerInstance = timeTrack[user]
    status = timerInstance.canSend()
    if not status:
      timeLeft = timerInstance.timeTillSend()
      bot.send_message(chat_id = message.chat.id, text = f"You have recently just posted a Question! Users are allowed to post one question every *3 minutes*, this is to prevent unnecessary spamming and overloading of our servers. Thank you for your cooperation! \n\nYou may post your next question in *{timeLeft}* seconds.", parse_mode = "Markdown")
      return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptQuestion, bot)
    return   

  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptQuestion, bot)
    return 

  # Retrieve QS instance from category_dic
  # Updates QS instance with question (user input, type: String)
  qns = fetch_question(message)
  qns.update_question(message.text)

  # Deserialize QS instance into bytestring representation. 
  # Store bytestring value into MongoDB.
  pickled_qns = pickle.dumps(qns) 

  # Creates post/document, insert into Database.
  try:
    post = {"_id": Question.id_counter, "status": qns.get_status(), "from_user": qns.get_from_user(), "category": qns.get_category(), "question": qns.get_question(), "instance": pickled_qns}
    if catQCount["updated"] == False:
      update_catQCount()
    collection.insert_one(post)
    Question.id_counter += 1

  # The exception we are trying to catch here is when QS instances are created with conflicting qID values.
  # Please refer to README document for detailed explanation on how this might happen.
  except:
    
    # Finding the largest existing qID in database allows us to continue assigning ID values to QS instances sequentially. 
    largest = findLargestID()
    Question.id_counter = largest + 1

    # Update catQCount dictionary with Question-Category count.
    if catQCount["updated"] == False:
      update_catQCount()

    # Creates post/document, insert into Database.
    post = {"_id": Question.id_counter, "status": qns.get_status(), "from_user": qns.get_from_user(), "category": qns.get_category(), "question": qns.get_question(), "instance": pickled_qns}
    collection.insert_one(post)
    
    Question.id_counter += 1

  finally:
    # Create new UserTimer instance to update time of latest Question post. 
    user = message.from_user.id
    timeTrack[user] = UserTimer(user, time.time())
    catQCount[qns.get_category()] += 1
    
    broadcast_message = f"*Category*: {code_to_cat_dict[qns.get_category()]}\n\n" + f"*Question* #*{Question.id_counter - 1}*:\n{qns.get_question()}\n\n" + f"To answer this question, go to the [UniHow Bot](https://t.me/unihow_bot) and send \n */ansid*. Following that, simply send *{Question.id_counter - 1}*."
    bot.send_message(chat_id = testchannelQN, text = broadcast_message, parse_mode= 'Markdown')
    bot.send_message(chat_id = message.chat.id, text = f"Thank you for your input, you question has been recorded on our [Question Broadcast Channel](https://t.me/UniHowQuestionChannel) for all to see! Your question number is *#{Question.id_counter - 1}*. Answers to your question will appear on our [Answer Broadcast Channel](https://t.me/testlink12345testlink). Be sure to look out for it!", parse_mode= 'Markdown')

