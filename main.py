import os
import telebot
from telebot.types import BotCommand
import csv
import emoji



my_secret = os.environ["MYPRECIOUS"]
bot = telebot.TeleBot(my_secret)


#read csv file
def read_csv(csvfilename):
  """
  Reads a csv file and returns a list of lists
  containing rows in the csv file and its entries.
  """
  with open(csvfilename, encoding='utf-8') as csvfile:
      rows = [row for row in csv.reader(csvfile)]
  return rows

#Set the commands in the main menu
bot.set_my_commands([
  BotCommand('start', 'Begin your UniHow journey!'),
  BotCommand('gipanel', 'Click here to learn all about NUS programs and accommodation options!'),
  BotCommand('askquestion', 'Send us your questions!'),
  BotCommand('ansquestion', 'Assist peers with their queries!'),
  BotCommand('livechat', 'Join our Chat Room!'),
  BotCommand('about', 'Find out more about UniHow!')
])

#Define start command in main menu 
@bot.message_handler(commands=['start'])
def start(message):
  """Welcome new User!"""
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to UniHow! \n\n/gipanel to view our General Information Panel! \n\n/askquestion if you want to ask a question! \n\n/ansquestion if you want to answer a question! \n\n/livechat to engage in a real-time conversation with a University senior or Professor!"
  bot.reply_to(message, messageReply)

#Define gipanel command in main menu 
@bot.message_handler(commands=['gipanel'])
def gipanel(message):
  """Shows the user the menu for gi panel """
  messageReply = emoji.emojize(f"This is the menu for our general information panel. Click on the links below to find out various information about NUS Undergraduate Programmes, Special Undergraduate Programmes, as well as accomodation options available in NUS.\n\n /ugprogrammes Undergraduate Programmes :school: \n\n /spprogrammes Special Undergraduate Programmes :school::star: \n\n /housing Accomodation on Campus :house:")
  bot.reply_to(message, messageReply)


#define Undergraduate Programmes menu 
@bot.message_handler(commands=['ugprogrammes'])
def ugprogrammes(message):
  """Undergraduate programmes/Faculties"""
  messageReply = emoji.emojize("Find out all about NUS Undergraduate Programmes here! Discover more about NUS Faculties and the degree courses they offer! \n\n/chs College of Humanities and Sciences :closed_book::microscope:\n\n/biz NUS Business School :briefcase:\n\n/computing School of Computing :laptop:\n\n/medicine Yong Loo Lin School of Medicine 	:stethoscope:\n\n/dentistry Faculty of Dentistry :tooth:\n\n/cde College of Design and Engineering :artist_palette::wrench:\n\n/law Faculty of Law :classical_building:\n\n/nursing Alice Lee Centre for Nursing Studies & Yong Loo Lin School of Medicine :syringe:\n\n/pharmacy Department of Pharmacy :pill:\n\n/music Yong Siew Toh Conservatory of Music :musical_note:")
  bot.reply_to(message, messageReply)

#Abstraction for the bot to reply based on "final" command 
def generateReply(input, filename, message):
  data = read_csv(filename)
  index = data[0].index(input)
  description = data[1][index]
  link = data[2][index]
  username = message.from_user.first_name
  greeting = emoji.emojize(f"Hi {username}! Welcome to {data[3][index]}! {data[4][index]} \n\n")
  text = f'Click [here]({link}) to find out more\!'
  bot.reply_to(message, greeting + description)
  bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')

  
#Defining all the commands within Undergraduate Programmes
@bot.message_handler(commands=['chs'])
def chs(message):
  """College of Humanities and Sciences"""
  generateReply('chs', 'faculties.csv', message)

@bot.message_handler(commands=['biz'])
def biz(message):
  """NUS School of Business"""
  generateReply('biz', 'faculties.csv', message)


@bot.message_handler(commands=['computing'])
def computing(message):
  """NUS School of Computing"""
  generateReply('computing', 'faculties.csv', message)


@bot.message_handler(commands=['dentistry'])
def dentistry(message):
  """NUS Faculty of Dentistry"""
  generateReply('dentistry', 'faculties.csv', message)

@bot.message_handler(commands=['cde'])
def cde(message):
  """NUS College of Design and Engineering"""
  generateReply('cde', 'faculties.csv', message)


@bot.message_handler(commands=['law'])
def law(message):
  """NUS Faculty of Law"""
  generateReply('law', 'faculties.csv', message)


@bot.message_handler(commands=['medicine'])
def medicine(message):
  """NUS Medicine"""
  generateReply('medicine', 'faculties.csv', message)


@bot.message_handler(commands=['nursing'])
def nursing(message):
  """NUS Nursing"""
  generateReply('nursing', 'faculties.csv', message)


@bot.message_handler(commands=['pharmacy'])
def pharmacy(message):
  """NUS Pharmacy"""
  generateReply('pharmacy', 'faculties.csv', message)


@bot.message_handler(commands=['music'])
def music(message):
  """NUS Music"""
  generateReply('music', 'faculties.csv', message)


  
#Define menu for Special Programmes 
@bot.message_handler(commands=['spprogrammes'])
def spprogrammes(message):
  """Special Undergraduate Programmes """
  messageReply = emoji.emojize(f"Click on the links below to find out various information about Special Undergraduate Programmes in NUS.\n\n/ddp Double Degree Programmes :rolled-up_newspaper::rolled-up_newspaper:\n\n/dmp Double Major Programmes :scroll::scroll:\n\n/cdp Concurrent Degree Programmes :rolled-up_newspaper::infinity::rolled-up_newspaper:\n\n/sp Special Programmes :star::rolled-up_newspaper:\n\n/jd Joint Degree Programmes :school::rolled-up_newspaper::school:\n\n/ptp Part Time Programmes :rolled-up_newspaper::eight-thirty:\n\n/mp Minor Programmes :scroll:")
  bot.reply_to(message, messageReply)

#Defining all the individual commands inside Special Programmes 

@bot.message_handler(commands=['ddp'])
def ddp(message):
  """Double Degree Programmes"""
  generateReply('ddp', 'spp.csv', message)

@bot.message_handler(commands=['dmp'])
def dmp(message):
  """Double Major Programmes"""
  generateReply('dmp', 'spp.csv', message)

@bot.message_handler(commands=['cdp'])
def cdp(message):
  """Concurrent Degree Programmes """
  generateReply('cdp', 'spp.csv', message)

@bot.message_handler(commands=['sp'])
def sp(message):
  """Special Programmes """
  messageReply = emoji.emojize("Welcome to NUS Special Programmes! Here you shall find unique and intriguing academic initiatives that are capable of making your University experience so much more enriching! Click on the various links below to find out more! \n\n/sep Student Exchange Programme :currency_exchange:\n\n/noc NUS Overseas Colleges :airplane:\n\n/usp University Scholars Programme :man_student:\n\n/utcp University Town College Programme :school:\n\n/rvrc Ridge View Residential College :houses:")
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['sep'])
def sep(message):
  """Student Exchange Programme"""
  generateReply('sep', 'spp.csv', message)

@bot.message_handler(commands=['noc'])
def noc(message):
  """NUS Overseas Colleges"""
  generateReply('noc', 'spp.csv', message)

@bot.message_handler(commands=['usp'])
def usp(message):
  """University Scholars Programme"""
  generateReply('usp', 'spp.csv', message)

@bot.message_handler(commands=['utcp'])
def utcp(message):
  """University Town College Programme"""
  generateReply('utcp', 'spp.csv', message)

@bot.message_handler(commands=['rvrc'])
def rvrc(message):
  """Ridge View Residential College"""
  generateReply('rvrc', 'spp.csv', message)

@bot.message_handler(commands=['jd'])
def jd(message):
  """Joint Degree Programmes"""
  generateReply('jd', 'spp.csv', message)

@bot.message_handler(commands=['ptp'])
def ptp(message):
  """Part-time Programmes"""
  generateReply('ptp', 'spp.csv', message)

@bot.message_handler(commands=['mp'])
def mp(message):
  """Minor Programmes"""
  generateReply('mp', 'spp.csv', message)

#Defining the menu for accommodation
@bot.message_handler(commands=['housing'])
def housing(message):
  """Accomodation on Campus"""
  messageReply = emoji.emojize(
        f"Looking for an opportunity to stay in campus? Craving for the 'full' uni-experience? You've come to the right place! Click on the links below to find out more about on-campus living and accomodation options in NUS.\n\n/halls Halls :house_with_garden:\n\n/houses Houses :house:\n\n/rc Residential Colleges :houses:\n\n/residences Residences :office_building:"
    )
  bot.reply_to(message, messageReply)
  text = 'Click [here](https://nus.edu.sg/osa/student-services/hostel-admission/undergraduate/application-guide) for more administrative information on NUS Hostel Admissions, such as Eligibility, Application Periods and Hostel Fees etc\!'
  bot.send_message(message.chat.id, text, parse_mode='MarkdownV2')

#Defining the individual commands for accommodation (halls)
@bot.message_handler(commands=['halls'])
def halls(message):
  """Hall"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Halls of Residences! \n\nExpect personal development opportunities through a myriad of co-curricular activities across sports, community engagement and cultural activities. Some General Education modules and Design-Your-Own-Module are offered here, with opportunities for elected student leadership via the Junior Common Room Committee (JCRC). Meal plans included. Here are NUS Hall options! \n\n/eusoff Eusoff Hall :eagle::blue_book:::white_flower: \n\n/kr Kent Ridge Hall :lion::books: \n\n/ke7 King Edward VII Hall :eagle:	:closed_book::lion: \n\n/raffles Raffles Hall :tiger::eagle: \n\n/sheares Sheares Hall :green_book::lion: \n\n/temasek Temasek Hall :lion::scroll:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['eusoff'])
def eusoff(message):
  """Eusoff Hall"""
  generateReply('eusoff', 'housing.csv', message)

@bot.message_handler(commands=['kr'])
def kr(message):
  """Kent Ridge Hall"""
  generateReply('kr', 'housing.csv', message)

@bot.message_handler(commands=['ke7'])
def ke7(message):
  """King Edward VII Hall"""
  generateReply('ke7', 'housing.csv', message)

@bot.message_handler(commands=['raffles'])
def raffles(message):
  """Raffles Hall"""
  generateReply('raffles', 'housing.csv', message)

@bot.message_handler(commands=['sheares'])
def sheares(message):
  """Sheares Hall"""
  generateReply('sheares', 'housing.csv', message)

@bot.message_handler(commands=['temasek'])
def temasek(message):
  """Temasek Hall"""
  generateReply('temasek', 'housing.csv', message)

#Defining the individual commands for accommodation (houses)
@bot.message_handler(commands=['houses'])
def houses(message):
  """House"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Houses! \n\nExpect lots of ground-up initiatives co-led by residents, peer mentorship, and a structured Proactive Pastoral Care (PPC) system – where every resident is assigned to a small yet robust support group. Collaborative student leadership roles are available as a Peer Mentor, Resident Assistant, or the Student Council. No meal plans. Currently there are two Houses. Explore them now! \n\n/lighthouse LightHouse :sun::house:\n\n/pioneer Pioneer House :palm_tree::lion:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['lighthouse'])
def lighthouse(message):
  """LightHouse"""
  generateReply('lighthouse', 'housing.csv', message)

@bot.message_handler(commands=['pioneer'])
def pioneer(message):
  """Pioneer House"""
  generateReply('pioneer', 'housing.csv', message)

#Defining the individual commands for accommodation (residential colleges)
@bot.message_handler(commands=['rc'])
def rc(message):
  """Residential Colleges"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Residential Colleges! \n\nExpect a diverse range of academic modules taught in intimate settings, dynamic and informal out-of-classroom learning, and student interest groups. Elected student leadership roles are available via the College Students’ Committee (CSC) and in interest groups. Meal plans included. Here are NUS Residential College Options! \n\n/rvrc Ridge View Residential College :four_leaf_clover: \n\n/capt College of Alice & Peter Tan :closed_book:::handshake::deciduous_tree:  \n\n/rc4 Residential College 4 :house::dolphin::light_bulb:\n\n/tembusu Tembusu College :evergreen_tree:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['capt'])
def capt(message):
  """College of Alice & Peter Tan"""
  generateReply('capt', 'housing.csv', message)

@bot.message_handler(commands=['rc4'])
def rc4(message):
  """Residential College 4"""
  generateReply('rc4', 'housing.csv', message)

@bot.message_handler(commands=['tembusu'])
def tembusu(message):
  """Tembusu College"""
  generateReply('tembusu', 'housing.csv', message)

#Defining the individual commands for accommodation (residences)
@bot.message_handler(commands=['residences'])
def residences(message):
  """Student Residences"""
  messageReply = emoji.emojize(
        f"Welcome to NUS Student Residences! \n\nResidents here have the option to participate in residential activities at a level that they are comfortable with. Programmes across themes of wellness, personal effectiveness, sports, cultural appreciation and community service are offered. Student leadership roles are available via the Resident Assistant and Cluster Leader role.  No meal plans. For speedy updates on your mobile phone, go to the uNivUS app, select 'Resources' and then 'Residential Living'. Currently, there are two Student Residences. Discover them now! \n\n/pgp PGP Residence :leaf_fluttering_in_wind: \n\n/utr UTown Residence :house_with_garden:"
    )
  bot.reply_to(message, messageReply)

@bot.message_handler(commands=['pgp'])
def pgp(message):
  """PGP Residence"""
  generateReply('pgp', 'housing.csv', message)

@bot.message_handler(commands=['utr'])
def utr(message):
  """UTown Residence"""
  generateReply('utr', 'housing.csv', message)
  
#Defining the Ask Question command 
@bot.message_handler(commands=['askquestion'])
def askQuestion(message):
  """Ask a Question! """
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Type your Question after this message!"
  bot.reply_to(message, messageReply)

#Defining the Answer Question command 
@bot.message_handler(commands=['ansquestion'])
def ansQuestion(message):
  """Answer a Question! """
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Type your Answer after this message!"
  bot.reply_to(message, messageReply)

#Defining the livechat command 
@bot.message_handler(commands=['livechat'])
def liveChat(message):
  """Enter Chat Room! """
  username = message.from_user.first_name
  messageReply = f"Hi {username}! Welcome to the Chat Room!"
  bot.reply_to(message, messageReply)

#Defining the About command 
@bot.message_handler(commands=['about'])
def about(message):
  username = message.from_user.first_name
  filename = "aboutUniHow.csv"
  data = read_csv(filename)
  messageReply = f"Hi {username}! "
  messageReply += data[1][0]
  bot.send_message(chat_id=message.chat.id, text=emoji.emojize(messageReply))


bot.infinity_polling()
