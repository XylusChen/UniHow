import os
import telebot
from pymongo import MongoClient
import pickle
from generalfunc import userEnd, go_back, containsProfanity, too_short, short_warning, profanity_warning


# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

@bot.message_handler(commands=['feedback'])
def feedback(message, bot):
  """Feedback"""
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to UniHow's Feedback Portal! You may send us your feedback after this message. Thank you!"
  current = bot.send_message(chat_id = message.chat.id, text = messageReply)
  bot.register_next_step_handler(current, acceptFeedback, bot)
  return

# Processing User's Feedback Input.
def acceptFeedback(message, bot):
  """Accepting a user's feedback"""
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our Feedback Portal! Come back anytime if you have more comments or suggestions for us!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptFeedback, bot)
    return 
  
  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptFeedback, bot)
    return 

  lastName = message.from_user.last_name
  firstName = message.from_user.first_name
  if lastName == None:
    name = firstName
  else:
    name = firstName + " " + lastName

  # Post Feedback to private Admin Channel.
  feedback = f"*From*: {name} \n\n*Feedback*: {message.text}"
  bot.send_message(chat_id = message.chat.id, text = "Thank you for your feedback! Your input has been successfully recorded. We greatly appreciate your efforts in helping us improve. Come back anytime if you have more comments or suggestions for us!")
  bot.send_message(chat_id = -1001541900629, text = feedback, parse_mode = "Markdown")

# Defining the report command.
@bot.message_handler(commands=['reportqna'])
def report(message, bot):
  """Report"""
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to UniHow's Report Portal! Before we begin, allow us to apologise for any unpleasant experience you may have had while using our QnA Forum. Rest assured that your report will be treated seriously and action will be taken against those who have misused our bot! \n\nPlease send us the Question ID of the question set you wish to submit a report against. Thank you!"
  
  current = bot.send_message(chat_id = message.chat.id, text = messageReply, parse_mode= 'Markdown')
  bot.register_next_step_handler(current, acceptReportQNA, bot)


# Process User's qID input.
def acceptReportQNA(message, bot):
    
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our report portal and for keeping the UniHow community safe! Come back again if you need to make a new report!")
    return

  try:
    lastName = message.from_user.last_name
    firstName = message.from_user.first_name
    if lastName == None:
      name = firstName
    else:
      name = firstName + " " + lastName

    # Retrieve reported QS from database using User Input (qID)
    qID = int(message.text)
    result = collection.find_one({"_id": qID})
    qns = pickle.loads(result["instance"])
    reported = f"*Reported by:* {name}\n\n*Category*: {qns.get_category()}\n\n" + f"*Question* #*{qID}*:\n{qns.get_question()}\n\n" + f"*Answer*:\n{qns.get_report()}"
    bot.send_message(chat_id = -1001541900629, text = reported, parse_mode= "Markdown")
    bot.send_message(chat_id = message.chat.id, text = "Thank you for filing a report. Your contribution has made the UniHow community a safer, more wholesome place!")

  # If User Input was invalid, search returns an error.
  except:
    current = bot.send_message(chat_id = message.chat.id, text = "Your input Question ID is *invalid*, please check that you have keyed in the correct Question ID. Thank you!", parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptReportQNA, bot)