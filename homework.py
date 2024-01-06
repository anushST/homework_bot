import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot

from exceptions import RequestError, ResponseKeysError

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

logging.basicConfig(
    level=logging.DEBUG,
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(message)s'
)

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def check_tokens():
    """Checks if the tokens are None."""
    if (PRACTICUM_TOKEN is None or TELEGRAM_CHAT_ID is None
            or TELEGRAM_TOKEN is None):
        logger.critical('Missing required environment variables')
        sys.exit()


def send_message(bot, message):
    """Sends message to bot."""
    # А это удачно проверять, что сообщение не отправленно ожиданием
    # исключения?
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.debug('Message sent succesfully')


def get_api_answer(timestamp):
    """Gets datas about homework."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    except Exception:
        raise RequestError('Server error')

    if response.status_code != HTTPStatus.OK:
        raise Exception('Incorrect status code')
    return response.json()


def check_response(response):
    """Checks response data according documentation."""
    if 'homeworks' not in response or 'current_date' not in response:
        raise TypeError('Keys not in response')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Response is not dict')


def parse_status(homework):
    """Returns status info."""
    try:
        homework_name = homework['homework_name']
        if homework['status'] not in HOMEWORK_VERDICTS:
            raise Exception('Unknow status')
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError:
        raise ResponseKeysError('Incorrect key(s) in response')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_showed = False

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response['current_date']
            if response['homeworks'] != []:
                message = parse_status(response['homeworks'][0])
                send_message(bot, message)
            else:
                logger.debug('No new status')
            error_showed = False
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.exception(error_message)
            try:
                if not error_showed:
                    send_message(bot, error_message)
                    error_showed = True
            except Exception:
                error_showed = True

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
