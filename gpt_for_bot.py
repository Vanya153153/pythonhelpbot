import requests
from transformers import AutoTokenizer
import logging
from config import *
from peremen import *

class GPT:
    def __init__(self, system_content="Ты - дружелюбный помощник для решения задач по python. "
                                      "Давай подробный ответ с решением на русском языке"):
        self.system_content = system_content
        self.URL = 'http://localhost:1234/v1/chat/completions'
        self.HEADERS = {"Content-Type": "application/json"}
        self.MAX_TOKENS = 200
        self.assistant_content = "Решим задачу по шагам: "

    # Подсчитываем количество токенов в промте
    @staticmethod
    def count_tokens(prompt):
        logging.info("Выевляем длину токенов в промте")
        tokenizer = AutoTokenizer.from_pretrained("Mistral-7B-Instruct-v0.2-GGUF")  # название модели
        return len(tokenizer.encode(prompt))

    def process_resp(self, response) -> [bool, str]:
        # Проверка статус кода
        logging.info("Проверяем статус код")
        if response.status_code < 200 or response.status_code >= 300:
            logging.error(
                f"Не удалось получить ответ, код состояния {response.status_code}"
            )
            return False, f"Ошибка: {response.status_code}"

        # Проверка json
        try:
            full_response = response.json()
        except:
            logging.error(
                f"Ошибка получения JSON, код состояния {response.status_code}"
            )
            return False, "Ошибка получения JSON"

        # Проверка сообщения об ошибке
        if "error" in full_response or 'choices' not in full_response:
            logging.error(
                f"Не получилось проверить, код состояния {response.status_code}"
            )
            return False, f"Ошибка: {full_response}"

        result = full_response['choices'][0]['message']['content']

        if result == "":
            return True, "Конец объяснения"
        logging.info("Возвращаем полученный результат")
        return True, result

    # Формирование промта
    def make_promt(self, user_history):
        logging.info("Берём макет и вставляем туда нужные нам параметры")
        json = {
            "messages": [
                {"role": "system", "content": user_history['system_content']},
                {"role": "user", "content": user_history['user_content']},
                {"role": "assistant", "content": user_history['assistant_content']}
            ],
            "temperature": 0.7,
            "max_tokens": self.MAX_TOKENS,
        }

        return json

    # Отправка запроса
    def send_request(self, json):
        logging.info("Отправка запроса")
        resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
        return resp

    # Сохраняем историю общения
    def save_history(self, assistant_content, content_response):
        logging.info("Сохраняем историю")
        return f"{assistant_content} {content_response}"

