import telebot
import strings
import config
from telebot import types
import user_data_manager
import datetime
import re
import time
from flask import Flask, request


bot = telebot.TeleBot(config.token, threaded=False)
# telebot.apihelper.proxy = {'https': 'socks5://127.0.0.1:9050'}

data_manager = user_data_manager.UserDataManager(config.db_file)
user_state = {}

bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url="https://minnakhmetov.pythonanywhere.com/{}".format(config.token))

app = Flask(__name__)


@app.route('/{}'.format(config.token), methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    print("Message")
    return "ok", 200


def get_text_schedule(user_id, day):
    arr = data_manager.get_day_schedule(user_id, day)
    text = "{}:\n".format(strings.day_names[day])
    for i in range(len(arr)):
        text += "{}. {}\n".format(str(i + 1), arr[i])
    return text


def get_main_menu_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    today = datetime.datetime.now().weekday()
    keyboard.row(types.InlineKeyboardButton(strings.today_button,
                                            callback_data="schedule_{}".format(str(today))),
                 types.InlineKeyboardButton(strings.tomorrow_button,
                                            callback_data="schedule_{}".format(str((today + 1) % 7))))
    keyboard.row(types.InlineKeyboardButton(strings.week_button,
                                            callback_data="schedule_week"),
                 types.InlineKeyboardButton(strings.edit_button,
                                            callback_data="edit"))
    return keyboard


def get_day_choice_keyboard():
    kb = types.InlineKeyboardMarkup()
    for i in range(7):
        kb.add(types.InlineKeyboardButton(strings.day_names[i],
                                          callback_data="edit_{}".format(str(i))))
    kb.add(types.InlineKeyboardButton(strings.back_to_main_menu_button,
                                      callback_data="main"))
    return kb


def get_lesson_choice_keyboard(cbq):
    path = cbq.data
    day = int(path.split("_")[1])
    lessons = data_manager.get_day_schedule(cbq.from_user.id, day)

    kb = types.InlineKeyboardMarkup()
    for i in range(8):
        kb.add(types.InlineKeyboardButton("{}. {}".format(str(i + 1), lessons[i]),
                                          callback_data="{}_{}".format(path, str(i))))
    kb.add(types.InlineKeyboardButton(strings.fill_day_button,
                                      callback_data="fill_{}".format(str(day))))
    kb.add(types.InlineKeyboardButton(strings.back_to_days_list_button,
                                      callback_data="edit"))
    return kb


def get_keyboard_for_schedule():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(strings.back_to_main_menu_button,
                                      callback_data="main"))
    return kb


def get_lesson_edit_keyboard(cbq):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(strings.name_button,
                                      callback_data="change_{}"
                                      .format(re.search(r"\d_\d", cbq.data).group()))),
    kb.add(types.InlineKeyboardButton(strings.delete_button,
                                      callback_data="delete_{}"
                                      .format(re.search(r"\d_\d", cbq.data).group()))),
    kb.add(types.InlineKeyboardButton(strings.back_to_lessons_list_button,
                                      callback_data=re.match(r"edit_\d", cbq.data).group()))
    return kb


def get_success_window_keyboard(day):
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton(strings.back_to_main_menu_button,
                                      callback_data="main"),
           types.InlineKeyboardButton(strings.back_to_lessons_list_button,
                                      callback_data="edit_{}".format(str(day))))
    return kb

@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"schedule_[0-6]", cbq.data))
def show_day_schedule(cbq):
    day = int(cbq.data[-1])
    bot.edit_message_text(get_text_schedule(cbq.from_user.id, day),
                          cbq.message.chat.id,
                          cbq.message.message_id,
                          reply_markup=get_keyboard_for_schedule())


@bot.callback_query_handler(
    lambda cbq: cbq.data == "schedule_week")
def show_week_schedule(cbq):
    text = ""
    for i in range(7):
        text += "{}\n\n".format(get_text_schedule(cbq.from_user.id, i))
    bot.edit_message_text(text,
                          cbq.message.chat.id,
                          cbq.message.message_id,
                          reply_markup=get_keyboard_for_schedule())


@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"edit", cbq.data))
def show_day_choice_menu(cbq):
    bot.edit_message_text(strings.choose_day_text,
                          cbq.message.chat.id,
                          cbq.message.message_id,
                          reply_markup=get_day_choice_keyboard())


@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"edit_[0-6]_[0-7]", cbq.data))
def show_lesson_edit_menu(cbq):
    bot.edit_message_text(strings.edit_menu_text,
                          cbq.message.chat.id,
                          cbq.message.message_id,
                          reply_markup=get_lesson_edit_keyboard(cbq))


@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"main", cbq.data))
def show_main_menu(cbq):
    bot.edit_message_text(strings.welcome_text,
                          cbq.message.chat.id,
                          cbq.message.message_id,
                          reply_markup=get_main_menu_keyboard())


@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"fill_[0-6]", cbq.data)
)
def fill_entire_day(cbq):
    user_state[cbq.from_user.id] = cbq.data
    bot.send_message(cbq.message.chat.id,
                     "{}\n\n{}".format(strings.how_to_fill_explanation_text,
                                       strings.fill_day_format))

@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"edit_[0-6]", cbq.data))
def show_lesson_choice_menu(cbq):
    bot.edit_message_text(strings.choose_lesson_text,
                          cbq.message.chat.id,
                          message_id=cbq.message.message_id,
                          reply_markup=get_lesson_choice_keyboard(cbq))


def show_success_changing_window(chat_id, day):
    bot.send_message(chat_id,
                     strings.successful_naming_text,
                     reply_markup=get_success_window_keyboard(day))


def show_success_deletion_window(chat_id, day):
    bot.send_message(chat_id,
                     strings.successful_deletion_text,
                     reply_markup=get_success_window_keyboard(day))


def show_success_filling_window(chat_id, day):
    bot.send_message(chat_id,
                     strings.successful_day_filling_text,
                     reply_markup=get_success_window_keyboard(day))

@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"change_[0-6]_[0-7]", cbq.data))
def change_lesson_name(cbq):
    user_state[cbq.from_user.id] = cbq.data
    bot.send_message(cbq.message.chat.id,
                     strings.enter_name_text)

@bot.callback_query_handler(
    lambda cbq: re.fullmatch(r"delete_[0-6]_[0-7]", cbq.data))
def delete_lesson(cbq):
    user_id = cbq.from_user.id
    day, num = map(int, re.findall(r"\d", cbq.data))
    data_manager.set_lesson(user_id, day, num, "")
    show_success_deletion_window(cbq.message.chat.id, day)


@bot.message_handler(commands=["start"])
def start_command(message):
    user_state[message.from_user.id] = "none"
    bot.send_message(message.chat.id,
                     strings.welcome_text,
                     reply_markup=get_main_menu_keyboard())


@bot.message_handler(content_types=["text"])
def handle_text_message(message):
    user_id = message.from_user.id
    if user_id not in user_state or \
            user_state[user_id] == "none":
        bot.send_message(message.chat.id, strings.warning_text)
    elif re.match(r"change", user_state[user_id]):
        if len(message.text) > 20:
            bot.send_message(message.chat.id, strings.wrong_name_length_text)
        else:
            day, num = map(int, re.findall(r"\d", user_state[user_id]))
            data_manager.set_lesson(user_id, day, num, message.text)
            user_state[user_id] = "none"
            show_success_changing_window(message.chat.id, day)
    elif re.match(r"fill", user_state[user_id]):
        if re.fullmatch(r"(.{1,20}(\r\n|\n|$)){1,8}", message.text):
            day = int(user_state[user_id][-1])
            user_state[user_id] = "none"
            lessons = message.text.splitlines()

            while len(lessons) < 8:
                lessons.append("")

            data_manager.set_day_schedule(user_id, day, lessons)
            show_success_filling_window(message.chat.id, day)

        else:
            bot.send_message(message.chat.id,
                             "{}\n\n{}".format(strings.wrong_day_format_text,
                                               strings.fill_day_format))