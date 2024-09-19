from asyncio import run as asyncio_run
from asyncio import sleep as asyncio_sleep
from asyncio import gather
from logging import basicConfig, getLogger, INFO
from os import environ
from datetime import date, datetime, timedelta
from re import search

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from requests import get as requests_get
from bs4 import BeautifulSoup


load_dotenv()

SCHEDULE_BASE_URL: str = environ.get('SCHEDULE_BASE_URL')
ENGLISH_TEACHER: str = environ.get('ENGLISH_TEACHER')

MARKDOWN_V2_RESERVED_CHARACTERS = '_*[]()~`>#+-=|{}.!'
BOT_WEEK_COMMANDS = {
    'get_previous': 'get_previous_week',
    'get_current': 'get_current_week',
    'reset_current': 'reset_current_week',
    'get_next': 'get_next_week',
}

active_messages: dict[int, Message] = {}
week_shifts: dict[int, int] = {}
dp = Dispatcher()

update_week_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='<', callback_data=BOT_WEEK_COMMANDS['get_previous']),
        InlineKeyboardButton(text='=', callback_data=BOT_WEEK_COMMANDS['get_current']),
        InlineKeyboardButton(text='⟳', callback_data=BOT_WEEK_COMMANDS['reset_current']),
        InlineKeyboardButton(text='>', callback_data=BOT_WEEK_COMMANDS['get_next']),
    ],
], resize_keyboard=True)


@dp.message(Command('help', 'start'))
async def start(message: Message) -> None:
    await message.reply(
        'Этот бот поможет тебе следить за расписанием занятий.'
        ' Он будет автоматически обновлять расписание каждые сутки, но ты можешь сделать это и сам в любой момент.'
        ' Также ты можешь перемещаться по расписанию на любое число недель вперёд и назад'
        ' (после можно сброситься до текущей недели).\n\n'
        f"Для начала напиши команду: /{BOT_WEEK_COMMANDS['get_current']}. Далее используй кнопки, bona mente!"
    )


def normalize_text(text: str) -> str:
    """
    Removes all \n, \r, large whitespaces (20 and 2 characters) from the given text.
    Escapes all Markdown v2 reserved characters.
    """

    text = text.replace('\n', '').replace('\r', '').replace(' ' * 20, '').replace('  ', '')

    for character in MARKDOWN_V2_RESERVED_CHARACTERS:
        text = text.replace(character, f'\\{character}')

    return text


def normalize_text_hard(text: str) -> str:
    """
    Removes all \\n, \\r, \\, whitespaces and Markdown reserved characters from the given text.
    """

    result = text.replace('\\', '').replace('\n', '').replace('\r', '').replace(' ', '')

    for character in MARKDOWN_V2_RESERVED_CHARACTERS:
        result = result.replace(character, '')

    return result


async def _get_week_schedule(chat_id: int) -> str:

    today_date = date.today()

    shifted_date = today_date + timedelta(weeks=week_shifts.get(chat_id, 0))
    shifted_date -= timedelta(days=shifted_date.weekday())  # normalization

    soup = BeautifulSoup(requests_get(
        f"{SCHEDULE_BASE_URL}/{shifted_date.strftime('%Y-%m-%d')}",
        headers={'Accept-Language': 'ru-RU,ru;q=0.9'},
    ).content, 'lxml')

    result = ''
    day_date = shifted_date

    for day_tag in soup.select('#accordion > div.panel.panel-default'):

        if day_date == today_date:
            day_circle = '🟢'

        elif day_date == today_date + timedelta(days=1):
            day_circle = '🟡'

        else:
            day_circle = '🔵'

        result += f"{day_circle} *{normalize_text(day_tag.select_one('div > h4').text).capitalize()}*\n"

        for lesson_tag in day_tag.select('ul > li'):

            lesson_tag_divs = lesson_tag.find_all('div', recursive=False)

            lesson_subject = lesson_tag_divs[1].select_one('div > div > span').text
            lesson_teacher = lesson_tag_divs[3].select_one('div > div > span').text

            if 'Английский язык' in lesson_subject and ENGLISH_TEACHER not in lesson_teacher:
                continue

            lesson_time_tag = lesson_tag_divs[0].select_one('div > div > span')

            is_cancelled = 'cancelled' in lesson_time_tag.get('class')

            result += (
                f"{'~' if is_cancelled else ''}"
                f"*{normalize_text(lesson_time_tag.text)}*"
                f" {normalize_text(lesson_subject)}"
            )

            if is_cancelled:
                result += '~'

            else:

                place_text = normalize_text(lesson_tag_divs[2].select_one('div > div > span').text)

                online_lesson_text = 'С использованием информационно\\-коммуникационных технологий'

                if online_lesson_text in place_text:
                    place_text = place_text.replace(online_lesson_text, f'__*{online_lesson_text.lower()}*__')

                elif cabinet_number := search(r'лит\\. .,', place_text):

                    cabinet_number_end = cabinet_number.end()

                    place_text = \
                        f"{place_text[:cabinet_number_end]} __*{place_text[cabinet_number_end:].replace(' ', '')}*__"

                result += f" {place_text} {normalize_text(lesson_teacher)}"

            result += '\n'

        result += '\n'
        day_date += timedelta(days=1)

    result += '_Обновлено: ' + datetime.now().strftime('%d\\.%M\\.%Y %H:%m:%S') + '_'

    return result


async def get_week_schedule(message: Message, week_shift: int = 0) -> None:

    if week_shifts.get(message.chat.id):
        week_shifts[message.chat.id] += week_shift

    else:
        week_shifts[message.chat.id] = week_shift

    week_schedule = await _get_week_schedule(message.chat.id)

    if active_message := active_messages.get(message.chat.id):

        if normalize_text_hard(week_schedule) != normalize_text_hard(active_message.text):
            active_messages[active_message.chat.id] = \
                await active_message.edit_text(
                    week_schedule, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=update_week_keyboard
                )

    else:

        message_reply = await message.reply(
            week_schedule, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=update_week_keyboard
        )

        await message_reply.bot.unpin_all_chat_messages(message_reply.chat.id)
        await message_reply.bot.pin_chat_message(message_reply.chat.id, message_reply.message_id)

        active_messages[message_reply.chat.id] = message_reply


@dp.callback_query(F.data == BOT_WEEK_COMMANDS['get_current'])
@dp.message(Command(BOT_WEEK_COMMANDS['get_current']))
async def get_current_week_schedule(event: Message | CallbackQuery) -> None:

    message = event if isinstance(event, Message) else event.message

    await get_week_schedule(message)


@dp.callback_query(F.data == BOT_WEEK_COMMANDS['get_next'])
@dp.message(Command(BOT_WEEK_COMMANDS['get_next']))
async def get_current_week_schedule(event: Message | CallbackQuery) -> None:

    message = event if isinstance(event, Message) else event.message

    await get_week_schedule(message, 1)


@dp.callback_query(F.data == BOT_WEEK_COMMANDS['get_previous'])
@dp.message(Command(BOT_WEEK_COMMANDS['get_previous']))
async def get_current_week_schedule(event: Message | CallbackQuery) -> None:

    message = event if isinstance(event, Message) else event.message

    await get_week_schedule(message, -1)


@dp.callback_query(F.data == BOT_WEEK_COMMANDS['reset_current'])
@dp.message(Command(BOT_WEEK_COMMANDS['reset_current']))
async def reset_schedule_current_week(event: Message | CallbackQuery) -> None:

    message = event if isinstance(event, Message) else event.message

    week_shifts[message.chat.id] = 0

    await get_week_schedule(message)


async def messages_updater() -> None:
    while True:

        for message in active_messages.values():

            new_text = await _get_week_schedule(message.chat.id)

            if normalize_text_hard(new_text) == normalize_text_hard(message.text):
                continue

            active_messages[message.chat.id] = \
                await message.edit_text(new_text, parse_mode=ParseMode.MARKDOWN_V2)

        sleep_time = (
                (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0) - datetime.now()
        ).seconds

        await asyncio_sleep(sleep_time)


async def main() -> None:

    basicConfig(level=INFO)

    logger = getLogger(__name__)

    if not (BOT_TOKEN := environ.get('BOT_TOKEN')):

        logger.error('The BOT_TOKEN environment variable is not set!')

        return

    for env_var_name, env_var_value in (
            ('SCHEDULE_BASE_URL', SCHEDULE_BASE_URL),
            ('ENGLISH_TEACHER', ENGLISH_TEACHER),
    ):
        if not env_var_value:

            logger.error(f'The "{env_var_name}" environment variable is not set!')

            return

    bot = Bot(token=BOT_TOKEN)

    await gather(dp.start_polling(bot), messages_updater())


if __name__ == '__main__':
    asyncio_run(main())
