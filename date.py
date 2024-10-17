import telebot
from datetime import datetime

token = '7456391675:AAGo4xaQd6-dF_8NaIQqB_PKstW1Km0v5vc'
bot = telebot.TeleBot(token)
@bot.message_handler(commands=['start'])
def start(message):    
    bot.reply_to(message, 'اهلا بك عزيزي انا بوت تفعيل البايو الوقتي فقط ارسل time/ في الكروب')
    
@bot.message_handler(commands=['time'])
def time(message):
    re = datetime.now()
    tim = re.strftime("time now : %H:%M:%S")
    bot.set_chat_description(message.chat.id, tim)
    bot.send_message(message.chat.id, 'تم تفعيل البايو الوقتي بنجاح.')


@bot.message_handler(commands=['date'])
def dat(message):
    dat = datetime.today()
    bot.reply_to(message, f'تاريخ اليوم :   {dat}')

print('runinng bot ')
bot.polling()
