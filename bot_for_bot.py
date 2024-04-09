from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from gpt_for_bot import GPT
from Players import file_user_id
from peremen import *

bot = TeleBot(API)


#Формат логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

# Функция для создания клавиатуры с нужными кнопочками
def create_keyboard(buttons_list):
    logging.info("Создание разных кнопок")
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


# Приветственное сообщение /start
@bot.message_handler(commands=['start'])
def start(message):
    logging.info("Отправка приветственного сообщения")
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    file_user_id(user_name, user_id)
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я бот-помощник для решения задач по программированию на python!\n"
                          f"Ты можешь прислать условие задачи, а я постараюсь её решить.\n"
                          "Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.",
                     reply_markup=create_keyboard(["/solve_task", '/help']))

# Команда /help
@bot.message_handler(commands=['help'])
def support(message):
    logging.info("Отправка вспомогательного сообщения")
    bot.send_message(message.from_user.id,
                     text="Чтобы приступить к решению задачи: нажми /solve_task, а затем напиши условие задачи",
                     reply_markup=create_keyboard(["/solve_task"]))


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    logging.info("Отправка сообщения просящего условия для задачи")
    bot.send_message(message.chat.id, "Напиши условие новой задачи:")
    bot.register_next_step_handler(message, get_promt)



# Фильтр для обработки кнопочки "Продолжить решение"
def continue_filter(message):
    logging.info("Отправка сообщения просящего условия для задачи")
    button_text = 'Продолжить решение'
    return message.text == button_text


# Получение задачи от пользователя или продолжение решения
@bot.message_handler(func=continue_filter)
def get_promt(message):
    logging.debug(f"Полученный текст от пользователя: {message.text}")
    user_id = message.from_user.id
    if message.content_type != "text":
        logging.warning("Получено пустое текстовое сообщение")
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, get_promt)
        return

    # Получаем текст сообщения от пользователя
    user_request = message.text
    if len(user_request) > MAX_LETTERS:
        logging.warning("Полученое текстовое сообщение превышает максимальную возможную длину")
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_promt)
        return


    if user_id not in users_history or users_history[user_id] == {}:
        logging.info("Сохраняем промт пользователя и начало ответа GPT в словарик users_history")
        users_history[user_id] = {
            'system_content': "Ты - дружелюбный помощник для решения задач по математике. Давай ответ с кратким решением на русском языке",
            'user_content': user_request,
            'assistant_content': "Решим задачу по шагам: "

        }

    logging.info(f"Создаём запрос")
    promt = GPT().make_promt(users_history[user_id])
    resp = GPT().send_request(promt)

    answer = ""
    logging.info(f"Проверяем код")
    answer = GPT().process_resp(resp)

    logging.debug(f"Прибавляем ответ в users_history[user_id]['assistant_content'] для будующей команды Продолжить")
    users_history[user_id]['assistant_content'] += str(answer)
    logging.info(f"Отправляем полученный ответ пользователю")
    bot.send_message(user_id, users_history[user_id]['assistant_content'],
                     reply_markup=create_keyboard(["Продолжить решение", "Завершить решение"]))

def end_filter(message):
    button_text = 'Завершить решение'
    return message.text == button_text


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Текущие решение завершено")
    users_history[user_id] = {}
    solve_task(message)
    if (user_id not in users_history or users_history[user_id] == {}) and message.text == "/Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить решение, сначала нужно отправить текст задачи")
        bot.send_message(user_id, "Напиши условие новой задачи:")
        bot.register_next_step_handler(message, get_promt)
        return

@bot.message_handler(commands=['debug'])
def send_logs(message):
    logging.info("Выдаём логи")
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(content_types=['text'])
def another_task(message):
    user_id = message.from_user.id
    logging.info("Бот реагирует на сообщение не являющеся командой")
    bot.send_message(user_id, 'Я не знаю что это значит, что я могу можно через команду /help')



if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling()

