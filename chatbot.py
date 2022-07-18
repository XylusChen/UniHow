import os
import telebot
import pymongo
from pymongo import MongoClient
from telebot import types
from telebot.types import BotCommand
from better_profanity import profanity

my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection_match = db["chatbot_match"]


# Detect Profanity in User Input.
def containsProfanity(message):
	if profanity.contains_profanity(message.text):
		return True
	return False

relationship_dic = {}


def check_true(chat_id, collection): 
	count = collection.count_documents({"id" : chat_id, "status" : "true" })
	if count == 1: 
		return True
	return False


def check_false(chat_id, collection): 
	count = collection.count_documents({"id" : chat_id, "status" : "false" })
	if count == 1: 
		return True
	return False


def check_searching(chat_id, collection): 
	count = collection.count_documents({"id" : chat_id, "status" : "searching" })
	if count == 1: 
		return True
	return False


def check_existing(chat_id, collection): 
	count = collection.count_documents({"id" : chat_id })
	if count == 1: 
		return True
	return False




def livechat(message):
	chat_id = message.chat.id 
	if check_true(chat_id, collection_match):

		bot.send_message(chat_id= chat_id, text= "You are in an active chat at the moment. Please send */endchat* to exit chat and then */livechat* to search for new chat.", parse_mode= "Markdown")
		return

	bot.send_message(chat_id= chat_id, text= "Welcome to *UniHow ChatRoom*! \n\nPlease be patient while we find someone to match you with!", parse_mode= "Markdown")

	if not check_existing(chat_id, collection_match): 
		input_user = {"id": chat_id,"status": "searching"}
		collection_match.insert_one(input_user)
	
	collection_match.update_one({"id" : chat_id}, {"$set": {"status" : "searching"}})
	available_users = {"status": "searching", "id" : {"$not" :{"$eq": chat_id}}}
	available_count = collection_match.count_documents(available_users) 

	if available_count == 0:
		bot.send_message(chat_id= chat_id, text = "There are no other users in the chatroom at the moment. Please wait and you will be matched once a new user joins the chatroom. To stop the search, send */stopsearch*. \n\nYou may continue using other UniHow features while waiting to be matched! You will be notified once we've found a match for you!", parse_mode= "Markdown")

		return 
		

	else: 
		other_user = collection_match.find_one(available_users)
		other_user_id = other_user["id"]
		collection_match.update_one({"id" : chat_id}, {"$set": {"status" : "true"}})
		collection_match.update_one({"id" : other_user_id}, {"$set": {"status" : "true"}})

		announcement_one = "You have been matched! Send a message now to start chatting!"
		announcement_two = "We hope to make this a safe environment for users to chat. Please avoid sending inapropriate messages. To report a chat, simply send */reportchat* while you are still in the chat.  The admins take the reports very seriously and will investigate accordingly."

		bot.send_message(chat_id= chat_id, text= announcement_one, parse_mode= "Markdown")
		bot.send_message(chat_id= chat_id, text= announcement_two, parse_mode= "Markdown")
		bot.send_message(chat_id= other_user_id, text= announcement_one, parse_mode= "Markdown")
		bot.send_message(chat_id= other_user_id, text= announcement_two , parse_mode= "Markdown")
		relationship_dic[chat_id] = other_user_id
		relationship_dic[other_user_id] = chat_id
		return 



def chatloop(message): 

	if containsProfanity(message):
		bot.send_message(chat_id = message.chat.id, text = "We have detected an inappropriate use of language in your previous message! Please behave reponsibly when using UniHow as we are trying to create a safe space for all users. Thank you for your cooperation.")
		return

	try: 
		other_user = relationship_dic[message.chat.id]
		bot.send_message(chat_id= other_user, text= message.text)

	except KeyError: 
		bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Send */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")

			

def resetchat(message): 
	collection_match.delete_many({})
	relationship_dic.clear()
	bot.send_message(chat_id= message.chat.id, text= " Reset MongoDB! Relationship dictionary cleared!", parse_mode= "Markdown")



def endchat(message):
	chat_id = message.chat.id 
	
	if not check_true(chat_id, collection_match): 
		bot.send_message(chat_id= chat_id, text= "You are not in an active chat at the moment, so there is no chat to end. Please send */livechat* to search for a new chat!", parse_mode= "Markdown")
		return

	my_id = message.chat.id
	other_user_id = relationship_dic[my_id]
	del relationship_dic[my_id]
	del relationship_dic[other_user_id]
	collection_match.update_one({"id" : my_id}, {"$set": {"status" : "false"}})
	collection_match.update_one({"id" : other_user_id}, {"$set": {"status" : "false"}})
	bot.send_message(chat_id= my_id, text = "You have left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")
	bot.send_message(chat_id= other_user_id, text = "The other user has left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")




def stopsearch(message):
	chat_id = message.chat.id 

	if check_true(chat_id, collection_match):
		bot.send_message(chat_id= message.chat.id, text = "You are in an active chat at the moment. Please send */endchat* to exit chat and then */livechat* to search for new chat.", parse_mode= "Markdown")
		return

	if not check_searching(chat_id, collection_match): 
		bot.send_message(chat_id= message.chat.id, text = "You are not searching for chats at the moment. Please send */livechat* to search for new chat.", parse_mode= "Markdown")
		return 


	collection_match.update_one({"id" : message.chat.id}, {"$set": {"status" : "false"}})
	bot.send_message(chat_id= message.chat.id, text = "Stopped searching for users. To search again, simply send */livechat*.", parse_mode= "Markdown")


def reportchat(message) : 
	try: 
		other_user_id = relationship_dic[message.chat.id]
		lastName = message.from_user.last_name
		firstName = message.from_user.first_name
		if lastName == None:
			name = firstName
		else:
			name = firstName + " " + lastName

		reportchattext = f"Reported by : {name} \n\n" + f"Suspect : {other_user_id}"
		bot.send_message(chat_id= -1001541900629, text = reportchattext, parse_mode= "Markdown")
	
	except KeyError: 
		bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Send */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")