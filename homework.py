import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import AnswerNot200Error, NoTokensError, RequestError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s '
                              '(def %(funcName)s:%(lineno)d)')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Checks if the tokens are None."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    }
    missing_tokens = {}
    for key, value in tokens.items():
        if value is None:
            missing_tokens[key] = value
    if missing_tokens:
        logger.critical('Missing required environment '
                        f'variables: {list(missing_tokens.keys())}')
        raise NoTokensError(f'No Token(s): {list(missing_tokens.keys())}')


def send_message(bot, message):
    """Sends message to bot."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Message sent succesfully')
    except Exception:
        logger.exception("Error while sending message to bot")


def get_api_answer(timestamp):
    """Gets datas about homework."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    except requests.RequestException:
        # А почему просто не оставить чтоб исключение RequestException
        # словилось в main
        raise RequestError('Something went wrong while getting data '
                           'from endpoint')

    if response.status_code != HTTPStatus.OK:
        raise AnswerNot200Error('Incorrect status code')
    return response.json()  # Обрабатывается в main()


def check_response(response):
    """Checks response data according documentation."""
    if not isinstance(response, dict):
        raise TypeError('Data is not dict')
    if 'homeworks' not in response:
        raise KeyError('Key "homeworks" is not in response')
    if 'current_date' not in response:
        logger.error('Key "current_date" is not in response')
    if not isinstance(response['current_date'], int):
        logger.error('"current_date" is not <int>')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Response is not dict')
    return response


def parse_status(homework):
    """Returns status info."""
    if 'homework_name' not in homework:
        raise ValueError('Dict "homework_name" is not in '
                         'response["homework"][0]')
    if 'status' not in homework:
        raise ValueError('Str "status" is not in response["homework"][0]')
    homework_name = homework['homework_name']
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise ValueError('Unknow status')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_msg = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            response = check_response(response)
            timestamp = response['current_date']
            if response['homeworks']:
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            else:
                logger.debug('No new status')
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.exception(error_message)
            if str(error) != last_error_msg:
                send_message(bot, error_message)
            last_error_msg = str(error)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
