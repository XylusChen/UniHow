import os
import telebot
import emoji
from pymongo import MongoClient
import pickle
from generalfunc import code_to_cat_dict, createCatMarkup, sendCategoryList, go_back, userEnd, too_short, validCategory, isReply, containsProfanity, go_back_message, short_warning, profanity_warning, catQCount, update_catQCount, broadcast_dic, five_posts, five_posts_announcement, not_number, not_number_text


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

def unanswered_quesV2(message, bot):

  if catQCount["updated"] == False:
    update_catQCount()
  
  total = 0
  for category in catQCount:
    if category == "updated":
      continue
    
    if catQCount[category] > 0:
      total += catQCount[category]
      bot.send_message(chat_id = message.chat.id, text = f"There are *{catQCount[category]}* unanswered questions in *{category}*", parse_mode = 'Markdown')

  # If there are no unanswered Questions across all Categories.
  if total == 0 :
    bot.send_message(chat_id = message.chat.id, text = "There are *no* unanswered questions at the moment. Feel free to come back later! ", parse_mode = 'Markdown')
    return

  else : 
    markup = createCatMarkup()
    last = bot.send_message(chat_id = message.chat.id, text = "The above are available categories with unanswered questions. Please reply with the category code to access them. \n\nFor example, if there are unanswered questions in 'medicine', I will respond with *medicine* to access the unanswered questions. To end, simply reply *end*.", reply_markup = markup, parse_mode = 'Markdown')
    bot.register_next_step_handler(last, filterCategoryAnswer, bot)
    
# Answering questions via Category 
@bot.message_handler(commands=['unanswered'])
def ansQuestion(message, bot):
  """Answer a Question! """
  username = message.from_user.first_name
  first = f"Hi {username}! Welcome to *UniHow QnA*! Below are all the available categories provided where other users can post questions under. You may then answer those questions."
  bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'Markdown')

  sendCategoryList(message)
  unanswered_quesV2(message, bot)

# Process User's Category selection.
def filterCategoryAnswer(message, bot):
  """Check validity of user's Category input"""
  
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, filterCategoryAnswer, bot)
    return
  
  category = message.text
  # If User input is Valid. 
  if validCategory(message):
    reply = f"You have selected *{category}*\. Please wait while we search for questions under this Category\."
    bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = "MarkdownV2")

    # Search for Question Sets through database. 
    # Matching Category, Unanswered.
    results_count = collection.count_documents({"status": False, "category": category})
    results = collection.find({"status": False, "category": category})
    
    # If there are no available questions
    if results_count == 0:
      reply = "Oops! There are no available questions of this category at the moment! Please try again later! \n\nIf you wish to select a new Category, please respond with the new Category code after this message. If you do not wish to answer a Question anymore, please type 'end'."
      markup = createCatMarkup()
      current = bot.send_message(chat_id = message.chat.id, text = reply, reply_markup = markup)
      bot.register_next_step_handler(current, filterCategoryAnswer, bot)
      return

    # Send Question to user, along with Question ID.
    for result in results:
      qID = result["_id"]
      id_text = f"*#{qID}*"
      q_string = result["question"]
      final = f"{q_string}\n\n{id_text}"
      bot.send_message(chat_id = message.chat.id, text = final, parse_mode = "Markdown")
    
    reply = "To answer a question, please reply the corresponding message with your answer using Telegram's reply function! To go back and select another question, simply send *back*. Thank you!"
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode= "Markdown")
    bot.register_next_step_handler(current, acceptAnswerCategory, bot)

  # If User input is invalid. 
  else:
    reply = "Your input is invalid\. Please respond with a valid Category Code\. Note that the codes are *case sensitive* and you *should not* include the quotation marks\. \n\nIf you do not wish to answer a Question anymore, please type 'end' after this message\."
    current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'MarkdownV2')
    bot.register_next_step_handler(current, filterCategoryAnswer, bot)


def acceptAnswerCategory(message, bot):
  """Accepting a user's Answer to existing Question"""

  if go_back(message):
    markup = createCatMarkup()
    current= bot.send_message(chat_id = message.chat.id, text = go_back_message, reply_markup = markup, parse_mode= "Markdown")
    bot.register_next_step_handler(current, filterCategoryAnswer, bot)
    return

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptAnswerCategory, bot)
    return
  
  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptAnswerCategory, bot)
    return 

  # Check if User's message is a Reply.
  if not isReply(message):
    current = bot.send_message(chat_id = message.chat.id, text = "We are unable to record your Answer as your input is not a *Reply* to one of our Questions\. Please make sure you are *replying to the message* corresponding to the question you are trying to answer\.", parse_mode = "MarkdownV2")
    bot.register_next_step_handler(current, acceptAnswerCategory, bot)
    return

  # Retrieve Original Message (contains the Question)
  question_message = isReply(message)
  message_string = question_message.text

  # Perform String split and indexing to retrieve qID.
  full = message_string.split("\n")
  qID_string = full[-1][1:]
  qID_int = int(qID_string)

  # Fetch QS from Database using qID as search filter.
  result = collection.find_one({"_id": qID_int})
  qns = pickle.loads(result["instance"])

  # Update QS instance with Answer and user_id.
  qns.update_answer(message.from_user.id, message.text)
  pickled_qns = pickle.dumps(qns)

  # Update post/document in database.
  collection.update_one({"_id": qID_int}, {"$set": {"instance": pickled_qns, "status": qns.get_status(), "answer_x5collection": qns.get_answerx5collection()}})

  if qns.get_answercount() >= 5 : 
    catQCount[qns.get_category()] -= 1

  bot.send_message(chat_id = message.chat.id, text = emoji.emojize("Your Answer has been successfully recorded! We would like to thank you for your contribution on behalf of the UniHow community! :smiling_face_with_smiling_eyes:. To view your answer, check out [UniHow Qna Broadcast Channel](https://t.me/UniHowQnA)."), parse_mode= 'Markdown')

  # Post completed QS Set to Broadcast Channel
  broadcast_message = f"*Category*: {code_to_cat_dict[qns.get_category()]}\n\n" + f"*Question* #*{qID_int}*:\n{qns.get_question()}\n\n" + f"*Answer*:\n{qns.get_answer(message.from_user.id)}"
  bot.send_message(chat_id = testchannelAns, text = broadcast_message, parse_mode= "Markdown")
  broadcast_dic["count"] += 1

  if five_posts(broadcast_dic) : 
    bot.send_message(chat_id = testchannelAns, text = five_posts_announcement, parse_mode= "Markdown")

    
#Answering questions via Question ID 
@bot.message_handler(commands=['ansid'])
def ansID(message, bot):
  """Answer a Question! """
  username = message.from_user.first_name
  first = f"Hi {username}! Welcome to *UniHow QnA*! To answer a question, please send us the question ID. This is indicated by the hashtag at the top of the question. For example, if I want to answer a question tagged #7, I will send *7*. Send the number now to answer the question. To end, simply send *end*."
  current = bot.send_message(chat_id = message.chat.id, text = first, parse_mode = 'Markdown')
  bot.register_next_step_handler(current, accept_question_number, bot)

# key : user ID, value: Question ID 
userID_to_QID_dict = {}

# accept question number from user
def accept_question_number(message, bot):
  """Accept valid question number from user"""
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if not_number(message.text): 
    current = bot.send_message(chat_id = message.chat.id, text = not_number_text)
    bot.register_next_step_handler(current, accept_question_number, bot)
    return

    # Search for Question Sets through database. 
    # Matching question ID, Unanswered.
  QID = int(message.text)
  results_count = collection.count_documents({"_id": QID, "status" : False})
  
    # If there are no available questions
  if results_count == 0:
      reply = "Oops! There is no active question tagged with this number right now. Please try again with a valid number. If you do not wish to answer a Question anymore, please type *end*."
      current = bot.send_message(chat_id = message.chat.id, text = reply, parse_mode = 'Markdown')
      bot.register_next_step_handler(current, accept_question_number, bot)
      return
  
  #Store QID based on user ID
  userID_to_QID_dict[message.from_user.id] = QID
  results = collection.find_one({"_id": QID})
    # Send Question to user, along with Question ID.
  category = results["category"]
  question = results["question"]
  message1 = "*The question you have selected is:* \n\n" + f"*Category*: {code_to_cat_dict[category]}\n\n" + f"*Question #{QID}*:\n{question}."
  bot.send_message(chat_id = message.chat.id, text = message1, parse_mode= 'Markdown')
  message2 = "To answer this question, send us your answer. To end, just send *end*. To go back and select a different question, just send *back*." 
  current = bot.send_message(chat_id = message.chat.id, text = message2, parse_mode= "Markdown")
  bot.register_next_step_handler(current, acceptAnswerID, bot)
      

# Process User's Answer input.
def acceptAnswerID(message, bot):
  """Accepting a user's Answer to existing Question"""

  if go_back(message) : 
    current = bot.send_message(chat_id = message.chat.id, text = go_back_message, parse_mode= "Markdown")
    bot.register_next_step_handler(current, accept_question_number, bot)
    return

  if userEnd(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our QnA forum! Come back anytime if you want to answer more questions!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptAnswerID, bot)
    return
  
  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptAnswerID, bot)
    return 
  
  #Retrieve QID based on user ID
  QID = userID_to_QID_dict[message.from_user.id]

  # Fetch QS from Database using qID as search filter.
  result = collection.find_one({"_id": QID})
  qns = pickle.loads(result["instance"])

  # Update QS instance with Answer and user_id.
  qns.update_answer(message.from_user.id, message.text)
  pickled_qns = pickle.dumps(qns)

  # Update post/document in database.
  collection.update_one({"_id": QID}, {"$set": {"instance": pickled_qns, "status": qns.get_status(), "answer_x5collection": qns.get_answerx5collection()}})

  if qns.get_answercount() >= 5 : 
    catQCount[qns.get_category()] -= 1

  bot.send_message(chat_id = message.chat.id, text = emoji.emojize("Your Answer has been successfully recorded! We would like to thank you for your contribution on behalf of the UniHow community! :smiling_face_with_smiling_eyes:. To view your answer, check out [UniHow Qna Broadcast Channel](https://t.me/UniHowQnA)."), parse_mode= 'Markdown')

  
  # Post completed QS Set to Broadcast Channel
  broadcast_message = f"*Category*: {code_to_cat_dict[qns.get_category()]}\n\n" + f"*Question* #*{QID}*:\n{qns.get_question()}\n\n" + f"*Answer*:\n{qns.get_answer(message.from_user.id)}"
  bot.send_message(chat_id = testchannelAns, text = broadcast_message, parse_mode= "Markdown")
  broadcast_dic["count"] += 1

  if five_posts(broadcast_dic) : 
    bot.send_message(chat_id = testchannelAns, text = five_posts_announcement, parse_mode= "Markdown")

