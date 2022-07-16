import os
import telebot
from random import randint

# Bot Token
my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)

user_ans_dic = {}

def get_operator(num):
  if num == 0:
    return "+"

  elif num == 1:
    return "-"

  else:
    return "*"
    
def get_answer(no1, no2, num):
  if num == 0:
    return no1 + no2

  if num == 1:
    return no1 - no2

  else:
    return no1 * no2

def startgame(message, bot):
  no1 = randint(0, 100)
  no2 = randint(0, 100)
  operator_num = randint(0, 3)
  operator = get_operator(operator_num)
  answer = get_answer(no1, no2, operator_num)
  user_ans_dic[message.from_user.id] = answer
  current = bot.send_message(chat_id = message.chat.id, text = f"{no1} {operator} {no2}")
  bot.register_next_step_handler(current, gameAnswer, bot)
  return

def gameAnswer(message, bot):
  if message.text.lower() == "end":
    bot.send_message(chat_id = message.chat.id, text = "Wow! Seems like elementary level Math is too hard for you! Get good.")
    return
    
  try:
    user_answer = int(message.text)
    if user_answer == user_ans_dic[message.from_user.id]:
      bot.send_message(chat_id = message.chat.id, text = "Wow! What a math god!")
      return

    else:
      current = bot.send_message(chat_id = message.chat.id, text = "How stupid are you??!")
      bot.register_next_step_handler(current, gameAnswer, bot)

  except ValueError:
    current = bot.send_message(chat_id = message.chat.id, text = "Haha very funny..")
    bot.register_next_step_handler(current, gameAnswer, bot)