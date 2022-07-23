import os
import telebot
from pymongo import MongoClient
from better_profanity import profanity
import pandas as pd
from generalfunc import go_back, containsProfanity, too_short



my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection_match = db["chatbot_match"]

#Adding more censored words to the blacklist 
csv_black_list = pd.read_csv('blacklist.csv')
column_to_read_from_csv = csv_black_list.words 
list_of_additional_words_to_blacklist = list(column_to_read_from_csv)
profanity.add_censor_words(list_of_additional_words_to_blacklist)

# Detect Profanity in User Input.
def containsProfanity(message):
	if profanity.contains_profanity(message.text):
		return True
	return False

#This dictionary stores 2 key-value pairs for each conversation matchup. For example, user A matched with user B, then two inputs are stored.
#This will allow us to find out the id of the other party from both ends. 
# { user A chat id : user B chat id }, { user B chat id : user A chat id }
relationship_dic = {}


#check status of each id in the database. key can be "true", "false" or "searching"
def check_collection(chat_id, collection, key): 
	count = collection.count_documents({"id" : chat_id, "status" : key })
	if count == 1: 
		return True
	return False

#check if id is even inside the database 
def check_existing(chat_id, collection): 
	count = collection.count_documents({"id" : chat_id })
	if count == 1: 
		return True
	return False



#start livechat feature 
def livechat(message):
	chat_id = message.chat.id 
	if check_collection(chat_id, collection_match, "true"):

		bot.send_message(chat_id= chat_id, text= "You are in an active chat at the moment. Please send */endchat* to exit chat and then */livechat* to search for new chat.", parse_mode= "Markdown")
		return

	bot.send_message(chat_id= chat_id, text= "Welcome to *UniHow ChatRoom*! \n\nPlease be patient while we find someone to match you with!", parse_mode= "Markdown")

	#if user is not already inside database
	if not check_existing(chat_id, collection_match): 
		input_user = {"id": chat_id}
		collection_match.insert_one(input_user)
	
	#set status to "searching" for this user
	collection_match.update_one({"id" : chat_id}, {"$set": {"status" : "searching"}})
	#count available users not inclusive of user searching (else count will always be at least 1)
	available_users = {"status": "searching", "id" : {"$not" :{"$eq": chat_id}}}
	available_count = collection_match.count_documents(available_users) 

	if available_count == 0:
		bot.send_message(chat_id= chat_id, text = "There are no other users in the chatroom at the moment. Please wait and you will be matched once a new user joins the chatroom. To stop the search, send */stopsearch*. \n\nYou may continue using other UniHow features while waiting to be matched! You will be notified once we've found a match for you!", parse_mode= "Markdown")

		return 
		

	else: 
		#retrieve other user id from database
		other_user = collection_match.find_one(available_users)
		other_user_id = other_user["id"]
		#set status of both users to "true"
		collection_match.update_one({"id" : chat_id}, {"$set": {"status" : "true"}})
		collection_match.update_one({"id" : other_user_id}, {"$set": {"status" : "true"}})

		announcement_one = "You have been matched! Send a message now to start chatting!"
		announcement_two = "We hope to make this a safe environment for users to chat. Please avoid sending inapropriate messages. To report a chat, simply send */reportchat* while you are still in the chat.  The admins take the reports very seriously and will investigate accordingly."

		bot.send_message(chat_id= chat_id, text= announcement_one, parse_mode= "Markdown")
		bot.send_message(chat_id= chat_id, text= announcement_two, parse_mode= "Markdown")
		bot.send_message(chat_id= other_user_id, text= announcement_one, parse_mode= "Markdown")
		bot.send_message(chat_id= other_user_id, text= announcement_two , parse_mode= "Markdown")
		#store 2 key-value pairs in the relationship dic 
		relationship_dic[chat_id] = other_user_id
		relationship_dic[other_user_id] = chat_id
		return 


#any message sent by the user that is not a command or a reply within a function (eg. answer question) will be sent to the other user currently matched via livechat (provided there is one)
def chatloop(message): 

	if containsProfanity(message):
		bot.send_message(chat_id = message.chat.id, text = "We have detected an inappropriate use of language in your previous message! Please behave reponsibly when using UniHow as we are trying to create a safe space for all users. Thank you for your cooperation.")
		return

	try: 
		#check if this user is currently matched with another user 
		other_user = relationship_dic[message.chat.id]
		bot.send_message(chat_id= other_user, text= message.text)

	except KeyError: 
		#if not matched with any other user 
		bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Send */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")

			
#admin command
def resetchat(message): 
	xylus = int(os.environ['Xylus_ID'])
	jay = int(os.environ['Jay_ID'])
	admin = [xylus, jay]
	if message.chat.id in admin:
		collection_match.delete_many({})
		relationship_dic.clear()
		bot.send_message(chat_id= message.chat.id, text= " Reset MongoDB chatbot! Relationship dictionary cleared!", parse_mode= "Markdown")


#for user to end chat
def endchat(message):
	chat_id = message.chat.id 
	
	#user must be in active chat to end chat 
	if not check_collection(chat_id, collection_match, "true"): 
		bot.send_message(chat_id= chat_id, text= "You are not in an active chat at the moment, so there is no chat to end. Please send */livechat* to search for a new chat!", parse_mode= "Markdown")
		return
	#access id pairs
	my_id = message.chat.id
	other_user_id = relationship_dic[my_id]
	#delete id pairs 
	del relationship_dic[my_id]
	del relationship_dic[other_user_id]
	#set status of both users to false 
	collection_match.update_one({"id" : my_id}, {"$set": {"status" : "false"}})
	collection_match.update_one({"id" : other_user_id}, {"$set": {"status" : "false"}})
	bot.send_message(chat_id= my_id, text = "You have left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")
	bot.send_message(chat_id= other_user_id, text = "The other user has left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")



#for user to stop searching for livechat 
def stopsearch(message):
	chat_id = message.chat.id 

	#check if user is already in a live chat 
	if check_collection(chat_id, collection_match, "true"):
		bot.send_message(chat_id= message.chat.id, text = "You are in an active chat at the moment. Please send */endchat* to exit chat and then */livechat* to search for new chat.", parse_mode= "Markdown")
		return

	#check if user is even searching 
	if not check_collection(chat_id, collection_match, "searching"): 
		bot.send_message(chat_id= message.chat.id, text = "You are not searching for chats at the moment. Please send */livechat* to search for new chat.", parse_mode= "Markdown")
		return 

	#update user status to false (stopped searching)
	collection_match.update_one({"id" : message.chat.id}, {"$set": {"status" : "false"}})
	bot.send_message(chat_id= message.chat.id, text = "Stopped searching for users. To search again, simply send */livechat*.", parse_mode= "Markdown")

#for user to report other party 
def reportchat(message) : 

	try:
		other_user_id = relationship_dic[message.chat.id]
		
		current = bot.send_message(chat_id= message.chat.id, text = "We are sorry that you had an unpleasant experience in our chatroom. Please provide a short description about why you wish to report the chat. To cancel this report, simply send *back*.", parse_mode= "Markdown")

		bot.register_next_step_handler(current, acceptchatreport)

	#if user is not in active chat at the moment 
	except KeyError:
		bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Send */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")


def acceptchatreport(message):

	if go_back(message):
		back_message = "You have returned to the livechat. You may continue chatting or make use of other UniHow features!"
		bot.send_message(chat_id = message.chat.id, text = back_message, parse_mode = "Markdown")
		return
	
	if containsProfanity(message):
		profanity_warning = "Your description contains inappropriate language. Please try again. "
		current = bot.send_message(chat_id = message.chat.id, text = profanity_warning, parse_mode = "Markdown")
		bot.register_next_step_handler(current, acceptchatreport)
		return 

	if too_short(message):
		short_warning = "Your description is too short. Please provide more information so we can look into it."
		current = bot.send_message(chat_id= message.chat.id, text = short_warning)
		bot.register_next_step_handler(current, acceptchatreport)
		return 

	else:
		other_user_id = relationship_dic[message.chat.id]
		lastName = message.from_user.last_name
		firstName = message.from_user.first_name
		if lastName == None:
			name = firstName
		else:
			name = firstName + " " + lastName

		reportchattext = "Live Chat report\n\n" + f"Reported by : {name} \n\n" + f"Suspect : {other_user_id}"
		bot.send_message(chat_id= -1001541900629, text = reportchattext, parse_mode= "Markdown")
	
