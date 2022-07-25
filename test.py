import os
import telebot
from pymongo import MongoClient
from generalfunc import validCats
import random
from qna import Question
from nospam import UserTimer
import time
import pickle

# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["testing"] 


# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)


relationship_dic = {}

#check status of each id in the database. key can be "true", "false" or "searching"
def check_collection(number, collection, key): 
	count = collection.count_documents({"_id" : number, "status" : key })
	if count == 1: 
		return True
	return False


def user_search(number, reply_tester):
	if check_collection(number, collection, "true"):

		bot.send_message(reply_tester, text= f"User {number} tried searching for a chat despite already being in one.", parse_mode= "Markdown")
		return


	collection.update_one({"_id" : number}, {"$set": {"status" : "searching"}})
	bot.send_message(reply_tester, text = f"User {number} is searching for a match." )
	available_users = {"status": "searching", "_id" : {"$not" :{"$eq": number}}}
	available_count = collection.count_documents(available_users) 

	if available_count == 0 :
		bot.send_message(reply_tester, text = f"User {number} tried searching for a match, but there were no other users." )
		return
	
	if available_count != 0:
		other_user = collection.find_one(available_users)
		other_user_no = other_user["_id"]
		#set status of both users to "true"
		collection.update_one({"_id" : number}, {"$set": {"status" : "true"}})
		collection.update_one({"_id" : other_user_no}, {"$set": {"status" : "true"}})
		bot.send_message(reply_tester, text = f"User {number} was matched with User {other_user_no}" )

		#store 2 key-value pairs in the relationship dic 
		relationship_dic[number] = other_user_no
		relationship_dic[other_user_no] = number
		return 

		

def end_chat(number, reply_tester): 
	
	
	if not check_collection(number, collection, "true"): 
		bot.send_message(reply_tester, text= f"User {number} tried to end the chat despite not being in an active chat.", parse_mode= "Markdown")
		return

	else :
		other_user_no = relationship_dic[number]
		#delete id pairs 
		del relationship_dic[number]
		del relationship_dic[other_user_no]
		#set status of both users to false 
		collection.update_one({"_id" : number}, {"$set": {"status" : "false"}})
		collection.update_one({"_id" : other_user_no}, {"$set": {"status" : "false"}})
		bot.send_message(reply_tester, text= f"User {number} ended the chat with User {other_user_no}", parse_mode= "Markdown")




def send_message(number, reply_tester):
	if not check_collection(number, collection, "true"):
		bot.send_message(reply_tester, text= f"User {number} tried sending a chat message despite not being in a chat.", parse_mode= "Markdown")
		return

	else:
		other_user_no = relationship_dic[number]
		bot.send_message(reply_tester, text= f"User {number} sent a message to User {other_user_no}.", parse_mode= "Markdown")
		return


#for user to stop searching for livechat 
def stopsearch(number, reply_tester):

	#check if user is already in a live chat 
	if check_collection(number, collection, "true"):
		bot.send_message(reply_tester, text = f"User {number} tried stopping search despite being in an active chat.", parse_mode= "Markdown")
		return

	#check if user is even searching 
	if not check_collection(number, collection, "searching"): 
		bot.send_message(reply_tester, text = f"User {number} is not searching but tried to end search.", parse_mode= "Markdown")
		return 

	#update user status to false (stopped searching)
	collection.update_one({"_id" :number}, {"$set": {"status" : "false"}})
	bot.send_message(reply_tester, text = f"User {number} stopped searching for a chat.", parse_mode= "Markdown")

#for user to report other party 
def reportchat(number, reply_tester) : 
	#if not matched with any other user
	if not check_collection(number, collection, "true"):
		bot.send_message(reply_tester, text= f"User {number} tried to report the chat despite not being in an active chat.", parse_mode= "Markdown")
		return

	else: 
		other_user_no = relationship_dic[number]
		bot.send_message(reply_tester, text = f"User {number} reported User {other_user_no}. ", parse_mode= "Markdown")






def test_chat(message): 
	#A list of random functions that can be generated, one per event
	my_list = [user_search, end_chat, send_message]
	#Generate a random number of users, from 2 users to 10 users
	no_users = random.randint(2,10)
	bot.send_message(message.chat.id, text = f"There are {no_users} users generated." )

	#total users = no_users
	#create user from 1 to no_users
	for i in range(1, no_users + 1):
		collection.insert_one({"_id" : i, "status" : "false"})
	

 #Decide number of events (random), 10-20 events
	no_events = random.randint(10,20)
	bot.send_message(message.chat.id, text = f"There will be {no_events} events simulated." )

	#simulate number of events
	for i in range(no_events): 
		#pick random user 
		user = random.randint(1,no_users)
		#pick random event to generate
		random.choice(my_list)(user, message.chat.id)

	collection.delete_many({})
	relationship_dic.clear()

	bot.send_message(message.chat.id, text = "Test ended." )

	return


















# Copy of tested function update_catQCount
def test_update_catQCount(dic):
	# Reset. All Question count set to 0.
	for cat in validCats:
		dic[cat] = 0
	dic["updated"] = False

	# Search for existing unanswered Questions in database.
	results_count = collection.count_documents({"status": False})
	results = collection.find({"status": False})

	# Database empty.
	if results_count == 0:
		dic["updated"] = True
		return

	# Update Question count for respective categories.
	for result in results:
		cat = result["category"]
		dic[cat] += 1
	dic["updated"] = True
	
	return dic


# Test function for update_catQCount
def test_func(message):

	# Dictionary to contain actual value of number of unanswered questions in category.
	ans_catQCount = {}
	for cat in validCats:
		ans_catQCount[cat] = 0

	# Dictionary to be passed into test_update_catQCount.
	test_catQCount = {}

	# No. of categories for this test run.
	num_of_cat = random.randint(1, len(validCats))

	# Shuffle the order of categories in list
	newCats = random.sample(validCats, num_of_cat)

	bot.send_message(chat_id = message.from_user.id, text = "Preparing database for testing. Please wait, this may take a while.")

	for cat in newCats:
		# No. of test questions to insert
		num_of_q = random.randint(1, 10)
		testq = f"This is a sample question about {cat}"
		
		# Insert test posts into database
		for i in range(0, num_of_q):
			testpost = {"status": False, "from_user": message.from_user.id, "category": cat, "question": testq}
			collection.insert_one(testpost)

		# Updating answer key dictionary with actual value
		ans_catQCount[cat] = num_of_q

	bot.send_message(chat_id = message.from_user.id, text = "Test questions upload complete.")
	
	# Running test_update_catQCount function
	test_update_catQCount(test_catQCount)

	# Comparing values in both dictionaries
	control = 0
	for cat in ans_catQCount:
		if cat == "updated":
			continue
			
		if ans_catQCount[cat] == test_catQCount[cat]:
			bot.send_message(chat_id = message.from_user.id, text = f"Test successful for {cat}. {test_catQCount[cat]} unanswered questions.")

		else:
			bot.send_message(chat_id = message.from_user.id, text = f"Test unsuccessful for {cat}. {ans_catQCount[cat]} in ans_catQCount VS {test_catQCount[cat]} in test_catQCount.")
			control += 1

	if control == 0:
		bot.send_message(chat_id = message.from_user.id, text = f"Test successful.")

	if control != 0:
		bot.send_message(chat_id = message.from_user.id, text = f"Test unsuccessful.")

	# Reset testing database collection.
	collection.delete_many({})
	bot.send_message(chat_id = message.from_user.id, text = f"Database reset!")
	return

	
# Test function for correct behaviour of Question and UserTimer class
def test_func_class(message):

	# Control variable to track number of test rounds failed.
	control = 0

	# Sample question
	question_sample = "This is a sample Question for class testing."
	
	bot.send_message(chat_id = message.chat.id, text = "Class Testing begin. Creating and uploading first QS instance into database.")

	# Creating and uploading first QS instance.
	first_qs = Question(message.from_user.id, "test_class")
	first_qs.update_question(question_sample)
	pickled_first_qs = pickle.dumps(first_qs)
	post = {"instance": pickled_first_qs}
	collection.insert_one(post)
	
	bot.send_message(chat_id = message.chat.id, text = "First QS instance uploaded, creating UserTimer instance. Changing INTERVAL to 10 seconds.")  

	# Setting INTERVAL to 10 seconds for test purposes.
	UserTimer.INTERVAL = 10

	# Creating UserTimer instance.
	timer_object = UserTimer(message.from_user.id, time.time())

	bot.send_message(chat_id = message.chat.id, text = "UserTimer instance created. Attempting to upload second QS instance into database in 3 seconds.") 

	time.sleep(3)

	# Round 1: Uploading second QS instance after 3 seconds. Upload should be unsuccessful.
	second_qs = Question(message.from_user.id, "test_class")
	second_qs.update_question(question_sample)
	pickled_second_qs = pickle.dumps(second_qs)
	post = {"instance": pickled_second_qs}
	status = timer_object.canSend()
	timeleft = timer_object.timeTillSend()
	if status:
		collection.insert_one(post)
		bot.send_message(chat_id = message.chat.id, text = "Round 1 unsuccessful. Second QS was uploaded into database when it should be blocked. Proceeding to round 2.")
		control += 1
	else:
		bot.send_message(chat_id = message.chat.id, text = f"Round 1 Successful. Second QS instance not uploaded. {timeleft} seconds left. Attempting to upload third QS instance into database in 3 seconds.")

	time.sleep(3)

	# Round 2: Uploading third QS instance after 3 seconds. Upload should be unsuccessful.
	third_qs = Question(message.from_user.id, "test_class")
	third_qs.update_question(question_sample)
	pickled_third_qs = pickle.dumps(third_qs)
	post = {"instance": pickled_third_qs}
	status = timer_object.canSend()
	timeleft = timer_object.timeTillSend()
	if status:
		collection.insert_one(post)
		bot.send_message(chat_id = message.chat.id, text = "Round 2 unsuccessful. Third QS was uploaded into database when it should be blocked. Proceeding to round 3.")
		control += 1
	else:
		bot.send_message(chat_id = message.chat.id, text = f"Round 2 Successful. Third QS instance not uploaded. {timeleft} seconds left. Attempting to upload final QS instance into database in 5 seconds.")  

	time.sleep(5)

	# Final Round: Uploading last QS instance after 5 seconds. Upload should be successful.
	last_qs = Question(message.from_user.id, "test_class")
	last_qs.update_question(question_sample)
	pickled_last_qs = pickle.dumps(last_qs)
	post = {"instance": pickled_last_qs}
	status = timer_object.canSend()
	if status:
		collection.insert_one(post)
		bot.send_message(chat_id = message.chat.id, text = "Round 3 Successful. Last QS instance uploaded. Executing database cleanup procedure.")  
	else:
		bot.send_message(chat_id = message.chat.id, text = "Round 3 unsuccessful. Last QS was uploaded into database when it should be blocked. Executing database cleanup procedure.")
		control += 1

	# Reset INTERVAL to 180 seconds (3 minutes).
	UserTimer.INTERVAL = 180
	bot.send_message(chat_id = message.chat.id, text = "INTERVAL reset to 180 seconds.")
	
	# Reset testing database collection.
	collection.delete_many({})
	bot.send_message(chat_id = message.from_user.id, text = f"Database reset!")

	if control == 0:
		bot.send_message(chat_id = message.from_user.id, text = f"Test Successful!")

	else:
		bot.send_message(chat_id = message.from_user.id, text = f"Test UnSuccessful! {control} rounds failed.")

	return
	
# Test function for correct behaviour of Question and UserTimer class
def test_func_class_random(message):

	# Control variable to track number of test rounds failed.
	control = 0

	# Sample question
	question_sample = "This is a sample Question for class testing."
	
	bot.send_message(chat_id = message.chat.id, text = "Random Class Testing begin. Creating and uploading first QS instance into database.")

	# Creating and uploading first QS instance.
	first_qs = Question(message.from_user.id, "test_class")
	first_qs.update_question(question_sample)
	pickled_first_qs = pickle.dumps(first_qs)
	post = {"instance": pickled_first_qs}
	collection.insert_one(post)

	random_interval = random.randint(10, 20)
	
	bot.send_message(chat_id = message.chat.id, text = f"First QS instance uploaded. Changing INTERVAL to {random_interval} seconds.")  

	# Setting INTERVAL to random_interval seconds for test purposes.
	UserTimer.INTERVAL = random_interval
	no_of_rounds = (random_interval // 3) - 1
	bot.send_message(chat_id = message.chat.id, text = f"Current test session will be executed {no_of_rounds + 1} rounds.")  
	
	# Creating UserTimer instance.
	timer_object = UserTimer(message.from_user.id, time.time())
	bot.send_message(chat_id = message.chat.id, text = "UserTimer instance created. Attempting to upload next QS instance into database in 3 seconds.") 

	# Each loop represents 1 round of attempt
	for i in range(0, no_of_rounds):
		time.sleep(3)

		# Round: Uploading QS instance after 3 seconds. Upload should be unsuccessful.
		qs = Question(message.from_user.id, "test_class")
		qs.update_question(question_sample)
		pickled_qs = pickle.dumps(qs)
		post = {"instance": pickled_qs}
		status = timer_object.canSend()
		timeleft = timer_object.timeTillSend()
		if status:
			collection.insert_one(post)
			bot.send_message(chat_id = message.chat.id, text = f"Round {i + 1} unsuccessful. QS was uploaded into database when it should be blocked. Proceeding to next round.")
			control += 1
		else:
			if i == no_of_rounds - 1:
				time_next = 5
				next = "final"
			else:
				time_next = 3
				next = "next"
			bot.send_message(chat_id = message.chat.id, text = f"Round {i + 1} Successful. QS instance not uploaded. {timeleft} seconds left. Attempting to upload {next} QS instance into database in {time_next} seconds.")


	time.sleep(5)

	# Final Round: Uploading last QS instance after 5 seconds. Upload should be successful.
	last_qs = Question(message.from_user.id, "test_class")
	last_qs.update_question(question_sample)
	pickled_last_qs = pickle.dumps(last_qs)
	post = {"instance": pickled_last_qs}
	status = timer_object.canSend()
	if status:
		collection.insert_one(post)
		bot.send_message(chat_id = message.chat.id, text = "Final Round Successful. Last QS instance uploaded. Executing database cleanup procedure.")  
	else:
		bot.send_message(chat_id = message.chat.id, text = "Final Round Unsuccessful. Last QS was uploaded into database when it should be blocked. Executing database cleanup procedure.")
		control += 1

	# Reset INTERVAL to 180 seconds (3 minutes).
	UserTimer.INTERVAL = 180
	bot.send_message(chat_id = message.chat.id, text = "INTERVAL reset to 180 seconds.")
	
	# Reset testing database collection.
	collection.delete_many({})
	bot.send_message(chat_id = message.from_user.id, text = f"Database reset!")

	if control == 0:
		bot.send_message(chat_id = message.from_user.id, text = f"Test Successful!")

	else:
		bot.send_message(chat_id = message.from_user.id, text = f"Test UnSuccessful! {control} rounds failed.")

	return
	
	
		