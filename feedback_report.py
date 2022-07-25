import os
import telebot
from pymongo import MongoClient
import pickle
from generalfunc import userEnd, go_back, containsProfanity, too_short, short_warning, profanity_warning
from chatbot import check_collection, relationship_dic


# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["unihow"] 
collection_match = db["chatbot_match"]

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
    report_content = ""
    report_dic = qns.get_report()

    for key in report_dic:
      report_content += f"{key}:\n" + report_dic[key] + "\n\n\n"


    reported = f"*Reported by:* {name}\n\n*Category*: {qns.get_category()}\n\n" + f"*Question* #*{qID}*:\n{qns.get_question()}\n\n" + f"*Answer*:\n" + report_content
    
    bot.send_message(chat_id = -1001541900629, text = reported, parse_mode= "Markdown")
    current = bot.send_message(chat_id = message.chat.id, text = "Thank you for filing a report. Your contribution has made the UniHow community a safer, more wholesome place! \n\nPlease let us know what was problematic with your reported Question Set by sending a short description after this message. If you do not wish to provide a description, simply send *end*.", parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptReportDescription, bot, qID)

  # If User Input was invalid, search returns an error.
  except:
    current = bot.send_message(chat_id = message.chat.id, text = "Your input Question ID is *invalid*, please check that you have keyed in the correct Question ID. Thank you!", parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptReportQNA, bot)


def acceptReportDescription(message, bot, qID):
  
  if userEnd(message) or go_back(message):
    bot.send_message(chat_id = message.chat.id, text = "Thank you for using our report portal and for keeping the UniHow community safe! Come back again if you need to make a new report!")
    return

  if containsProfanity(message):
    current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
    bot.register_next_step_handler(current, acceptReportDescription, bot, qID)
    return 
  
  if too_short(message):
    current = bot.send_message(chat_id= message.chat.id, text = short_warning)
    bot.register_next_step_handler(current, acceptReportDescription, bot, qID)
    return 

  lastName = message.from_user.last_name
  firstName = message.from_user.first_name
  if lastName == None:
    name = firstName
  else:
    name = firstName + " " + lastName    

  reported = f"*From*: {name} \n\n*Reported Question*: {qID} \n\n*Description*: {message.text}"
  bot.send_message(chat_id = -1001541900629, text = reported, parse_mode= "Markdown")
  bot.send_message(chat_id = message.chat.id, text = "Your input has been recorded! Thank you for your report submission!", parse_mode= "Markdown")
  return


#for user to report other party 
def reportchat(message, bot) : 
	#if not matched with any other user
	if not check_collection(message.chat.id, collection_match, "true"):
		bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Send */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")
		return

	else: 
		current = bot.send_message(chat_id= message.chat.id, text = "We are sorry that you had an unpleasant experience in our chatroom. Please provide a short description about why you wish to report the chat. To cancel this report, simply send *back*.", parse_mode= "Markdown")

		bot.register_next_step_handler(current, acceptchatreport, bot)




def acceptchatreport(message, bot):

	if go_back(message):
		back_message = "You have returned to the livechat. You may continue chatting or make use of other UniHow features!"
		bot.send_message(chat_id = message.chat.id, text = back_message, parse_mode = "Markdown")
		return
	
	if containsProfanity(message):
		profanity_warning = "Your description contains inappropriate language. Please try again. "
		current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
		bot.register_next_step_handler(current, acceptchatreport, bot)
		return 

	if too_short(message):
		short_warning = "Your description is too short. Please provide more information so we can look into it."
		current = bot.send_message(chat_id= message.chat.id, text = short_warning)
		bot.register_next_step_handler(current, acceptchatreport, bot)
		return 

	else:
		other_user_id = relationship_dic[message.chat.id]
		lastName = message.from_user.last_name
		firstName = message.from_user.first_name
		if lastName == None:
			name = firstName
		else:
			name = firstName + " " + lastName

		reportchattext = "Live Chat report\n\n" + f"Reported by : {name} \n\n" + f"Suspect : {other_user_id}\n\n" + f"Description: {message.text}"
		bot.send_message(chat_id= -1001541900629, text = reportchattext, parse_mode= "Markdown")
		success_report = "Your report has been submitted. Thank you for keeping the UniHow community safe. To end the chat, send /endchat."
		bot.send_message(chat_id = message.chat.id, text = success_report, parse_mode= "Markdown")
		return 
	
