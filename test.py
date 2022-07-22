import os
import telebot
from pymongo import MongoClient
from generalfunc import validCats
import random

# MongoDB database integration
db_secret = os.environ['MongoDB_Token']
cluster = MongoClient(db_secret)
db = cluster["telegram"]
collection = db["testing"] 

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)


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
  

  

    