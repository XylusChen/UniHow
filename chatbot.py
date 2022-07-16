import os
import telebot
import pymongo
from pymongo import MongoClient
from telebot import types
from telebot.types import BotCommand

my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

cluster = MongoClient("mongodb+srv://unihow:unihow@cluster0.ed1i7.mongodb.net/?retryWrites=true&w=majority")
db = cluster["telegram"]
collection = db["chatbot"] 

counter = {"counter": 0}
relationship_dic = {}

def startchat(message):
    chat_id = message.chat.id 
    bot.send_message(chat_id= chat_id, text= "We are currently matching you with another user.", parse_mode= "Markdown")

    check_existing = collection.count_documents({"id":chat_id})

    if check_existing == 0: 
      input_user = {"No.": counter["counter"],"id": chat_id,"status": "false" }
      collection.insert_one(input_user)
      counter["counter"] += 1
    
    available_users = {"status": "false", "id" : {"$not" :{"$eq": chat_id}}}
    available_count = collection.count_documents(available_users) 

    if available_count == 0:
        bot.send_message(chat_id= chat_id, text= "There are no users at the moment. Please wait and you will be matched eventually. To stop the search, send */stopsearch*. \n\nYou may continue using other UniHow features while waiting to be matched! Our bot will notify you when a chat partner is found!", parse_mode= "Markdown")

        return 
        

    else: 
        other_user = collection.find_one(available_users)
        other_user_id = other_user["id"]
        collection.update_one({"id" : chat_id}, {"$set": {"status" : "true"}})
        collection.update_one({"id" : other_user_id}, {"$set": {"status" : "true"}})
        bot.send_message(chat_id= chat_id, text= "You have been matched! Send a message now to start chatting!", parse_mode= "Markdown")
        bot.send_message(chat_id= other_user_id, text= "You have been matched! Send a message now to start chatting!", parse_mode= "Markdown")
        relationship_dic[chat_id] = other_user_id
        relationship_dic[other_user_id] = chat_id
        return 



def chatloop(message): 
    if message.text == "/startchat":
        startchat(message)
        return
    
    if message.text == "/reset":
        reset(message)
        return
    
    if message.text == "/endchat":
        endchat(message)
        return 

    if message.text == "/stopsearch":
        stopsearch(message)
        return 

    try: 
        other_user = relationship_dic[message.chat.id]
        bot.send_message(chat_id= other_user, text= message.text)

    except KeyError: 
        bot.send_message(chat_id= message.chat.id, text= "You are not matched with any user at the moment. Type */livechat* to start searching for a user to chat with!", parse_mode= "Markdown")

            

def reset(message): 
    counter["counter"] = 0
    collection.delete_many({})
    bot.send_message(chat_id= message.chat.id, text= "Reset counter! Reset MongoDB! Dictionary cleared!", parse_mode= "Markdown")
    relationship_dic.clear()



def endchat(message):
    my_id = message.chat.id
    other_user_id = relationship_dic[my_id]
    del relationship_dic[my_id]
    del relationship_dic[other_user_id]
    collection.delete_one({"id" : my_id})
    collection.delete_one({"id" : other_user_id})
    bot.send_message(chat_id= my_id, text = "You have left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")
    bot.send_message(chat_id= other_user_id, text = "The other user has left the chat. Send */livechat* to search for another chat!", parse_mode= "Markdown")




def stopsearch(message):
    collection.delete_one({"id": message.chat.id})
    bot.send_message(chat_id= message.chat.id, text = "Stopped searching for users. To search again, simply send */livechat*.", parse_mode= "Markdown")

