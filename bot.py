import telebot
import pymysql
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from time import sleep

from resources import config

bot = telebot.TeleBot(config.token)

emojis = {
    'rock'     : '👊', 
    'scissors' : '✌️',
    'paper'    : '✋',
}

win_matrix = {
    #user1        #user2
    'rock'     :  {'rock': 0, 'paper' : 2, 'scissors' : 1}, 
    'paper'    :  {'rock': 1, 'paper' : 0, 'scissors' : 2},
    'scissors' :  {'rock': 2, 'paper' : 1, 'scissors' : 0},
}

db_name = config.db_name
db_pass = config.db_pass
db_host = config.server

kb = InlineKeyboardMarkup(row_width = 3)
kb.add(
    InlineKeyboardButton("👊", callback_data = "rock"),
    InlineKeyboardButton("✌️", callback_data = "scissors"),
    InlineKeyboardButton("✋", callback_data = "paper")
)

@bot.inline_handler(lambda query: len(query.query) == 0)
def default_query(inline_query):
    try:
        game_message = types.InputTextMessageContent("Ожидаем игроков...\n ... VS ...")

        r = types.InlineQueryResultArticle(
            id = '2', 
            title = "RPS", 
            description = "Inline rock-paper-scissors", 
            input_message_content = game_message, 
            reply_markup = kb
        )

        bot.answer_inline_query(inline_query.id, [r])

    except Exception as e:
        print(e)

@bot.callback_query_handler(func = lambda call: True)
def callback_inline(call):
    mess = "Ожидаем игроков...\n ... VS ..."

    if call.inline_message_id:
        con = pymysql.connect(
            host = db_host, 
            user = db_name,
            password = db_pass, 
            database = db_name,
        )

        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM Games WHERE game_id = \"{0}\"".format(call.inline_message_id))
            row = cur.fetchone()
            
            if row is None:
                new_mess = mess.replace("... VS", "{0} VS".format(call.from_user.first_name))
                try:
                    cur.execute("INSERT INTO `Games`(`game_id`, `user1_id`, `user1_name`, `user1_choice`) VALUES (\"{0}\", \"{1}\", \"{2}\", \"{3}\") ".format(
                        call.inline_message_id, call.from_user.id, call.from_user.first_name, call.data
                    ))
                    con.commit()
                except:
                    bot.answer_callback_query(call.id, text = "Миша, всё хуйня, давай по новой 😌")
                    bot.edit_message_text(inline_message_id = call.inline_message_id, text = "Ожидаем бухгалтера...\n Пупа VS Лупа", reply_markup = kb)
                    return
                
                bot.edit_message_text(inline_message_id = call.inline_message_id, text = new_mess, reply_markup = kb)                
                
                bot.answer_callback_query(call.id, text = "Ты выбрал " + emojis[call.data])
            else:
                if str(call.from_user.id) == str(row[1]):
                    bot.answer_callback_query(call.id, text = "Ты уже в игре, дурашка)")
                else:
                    bot.answer_callback_query(call.id, text = "Ты выбрал " + emojis[call.data])

                    res = win_matrix[row[3]][call.data]                    
                    
                    if res == 0:
                        mess = '👾 Ничья 👾'
                    elif res == 1:
                        mess = '🎉 Победил ' + row[2] + ' 🎉'
                    else:
                        mess = '🎉 Победил ' + call.from_user.first_name + ' 🎉'

                    mess += '\n\n{0} - {1}\n{2} - {3}'.format(
                        row[2], emojis[row[3]],
                        call.from_user.first_name, emojis[call.data] 
                    ) 

                    cur.execute("DELETE FROM `Games` WHERE `game_id` = \"{0}\"".format(call.inline_message_id))
                    con.commit();  

                    bot.edit_message_text(inline_message_id = call.inline_message_id, text = mess)


bot.infinity_polling(True)
