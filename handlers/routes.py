from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import sqlite3
import hashlib
import datetime
import pytz
from uuid import uuid4


router = Router()

# Создание базы данных -------------------------------------------------------------

# Инициализация базы данных
conn = sqlite3.connect('subjects_homework.db')
cursor = conn.cursor()

# Создаём таблицу, если ещё нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    homework TEXT
)
''')
conn.commit()

# Функции для работы с предметами
def get_homework(subject_name):
    cursor.execute('SELECT homework FROM subjects WHERE name=?', (subject_name,))
    res = cursor.fetchone()
    if res:
        return res[0]
    else:
        # Если предмета нет, можно создать его с пустым домашним заданием или вернуть сообщение
        return 'Нет'

def set_homework(subject_name, hw_text):
    # Попытка обновить
    cursor.execute('UPDATE subjects SET homework=? WHERE name=?', (hw_text, subject_name))
    if cursor.rowcount == 0:
        # Если предмета нет — добавим
        cursor.execute('INSERT INTO subjects (name, homework) VALUES (?, ?)', (subject_name, hw_text))
    else:
        # Обновление прошло успешно
        pass
    conn.commit()

def get_all_homeworks():
    cursor.execute('SELECT name, homework FROM subjects')
    return cursor.fetchall()  # Возвращает список кортежей [(name, homework), ...]

# Время ------------------------------------------------------------------------------

def get_time():
    region = pytz.timezone('Europe/Astrakhan')

    current_time = datetime.datetime.now(region)

    tomorrow = current_time + datetime.timedelta(days=1)
    year_str = current_time.strftime('%Y')
    year = str(int(year_str) - 2000)
    date_str = current_time.strftime(f'%d.%m.{year}')
    date_tommorow_str = tomorrow.strftime(f'%d.%m.{year}')
    time_str = current_time.strftime('%H:%M:%S')
    day_of_week_str = current_time.strftime('%A')
    hour_str = current_time.strftime('%H')
    day_str = current_time.strftime('%d')
    return {
        'date_str': date_str,
        'date_tommorow_str': date_tommorow_str,
        'time_str': time_str,
        'day_of_week_str': day_of_week_str,
        'hour_str': hour_str,
        'day_str': day_str
    }




# Кнопочки --------------------------------------------------------------------------------------------------------- 

def get_main_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Расписание')],
        ],
        resize_keyboard=True
    )

    return keyboard


# Сообщения боту --------------------------------------------------------------------------------------------------------- 

@router.message(Command('start'))
async def start(message: Message):
    await message.answer(f'привет, я - персональный помощник группы пб-11\n/help - навигация', parse_mode='HTML', reply_markup=get_main_reply_keyboard())

@router.message(Command('test'))
async def test(message: Message):
    await message.answer(f'{time['time_str']}')

@router.message(F.text == 'Расписание')
async def command_keyboard_handler(message: Message):
    await message.answer_photo(f'https://www.dropbox.com/scl/fi/f2z338t70quvmalnhpsxg/Screenshot_4.png?rlkey=ebjlkw75jicesx1bypemcdhhz&st=rixawmf1&dl=0', caption='расписание на всю неделю:')

@router.message(Command("hw"))
async def show_homework(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("укажи предмет: /hw предмет")
        return
    subject = parts[1].strip()
    hw = get_homework(subject)
    await message.answer(f"домашнее задание по дисциплине {subject}:\n{hw}")

@router.message(Command('sethw'))
async def set_homework_command(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("укажи предмет и дз по примеру: /sethw предмет, домашнее задание")
        return
    subject = parts[1].strip()
    hw_text = parts[2].strip()
    set_homework(subject, hw_text)
    await message.answer(f"домашнее задание по дисциплине {subject} обновлено:\n{hw_text}")

@router.message(Command("allhw"))
async def show_all_homeworks(message: Message):
    rows = get_all_homeworks()
    if not rows:
        await message.answer("домашних заданий пока нет.")
        return

    # Формируем ответ
    reply_text = "все домашние задания:\n"
    for subject, hw in rows:
        reply_text += f"\n📝 {subject}: {hw}"

    await message.answer(reply_text)

@router.message(Command('help'))
async def help(message: Message):
    await message.answer('список доступных команд у бота:\n\n/hw - домашнее задание по какому-либо предмету\n/sethw - написать/обновить домашнее задание по какому-либо предмету\n/allhw - список всех известных домашних заданий')

# Инлайн-запросы --------------------------------------------------------------------------------------------------------- 

time = get_time()

if time['day_of_week_str'] == 'Monday':
    schedule_day_of_week_str = f'Сегодня {time['date_str']}, понедельник. \n\n1.\n<b>История</b>\n<u>8:30 - 10:05</u>\n<blockquote>424 аудитория\nДз: {get_homework('история')}</blockquote>\n\n2\n<b>Физкультура</b>\n<u>10:15 - 11:50</u>\n<blockquote>Спортивный зал</blockquote>\n\n3.\n<b>Английский язык</b>\n<u>12:20 - 13:55</u>\n<blockquote>413 аудитория - 1 группа\nДз: {get_homework('англ1')}\n314 аудитория - 2 группа\nДз: {get_homework('англ2')}</blockquote>\n\n4\n<b>Русский язык</b>\n<u>14:10 - 15:45</u>\n<blockquote>309 аудитория\n {get_homework('русский')}</blockquote>'

    tommorow_schedule_day_of_week_str = f'Завтра {time['date_tommorow_str']}, вторник. \n\n1.\n<b>Литература</b>\n<u>8:30 - 10:05</u>\n<blockquote>309 аудитория\nДз: {get_homework('литература')}</blockquote>\n\n2\n<b>Физика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('физика')}</blockquote>\n\n3.\n<b>История</b>\n<u>12:20 - 13:55</u>\n<blockquote>424 аудитория\nДз: {get_homework('история')}</blockquote>\n\n4.\n<b>Информатика</b>\n<u>14:10 - 15:45</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>'

elif time['day_of_week_str'] == 'Tuesday':
    schedule_day_of_week_str = f'Сегодня {time['date_str']}, вторник. \n\n1.\n<b>Литература</b>\n<u>8:30 - 10:05</u>\n<blockquote>309 аудитория\nДз: {get_homework('литература')}</blockquote>\n\n2\n<b>Физика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('физика')}</blockquote>\n\n3.\n<b>История</b>\n<u>12:20 - 13:55</u>\n<blockquote>424 аудитория\nДз: {get_homework('история')}</blockquote>\n\n4\n<b>Информатика</b>\n<u>14:10 - 15:45</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>'

    tommorow_schedule_day_of_week_str = f'Завтра {time['date_tommorow_str']}, среда. \n\n1.\n<b>Математика</b>\n<u>8:30 - 10:05</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>\n\n2\n<b>Информатика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>\n\n3.\n<b>Литература</b>\n<u>12:20 - 13:55</u>\n<blockquote>309 аудитория\nДз: {get_homework('литература')}</blockquote>\n\n4.<b>Обществознание</b>\n<u>14:10 - 15:45</u>\n<blockquote>424 аудитория\nДз: {get_homework('обществознание')}</blockquote>'

elif time['day_of_week_str'] == 'Wednesday':
    schedule_day_of_week_str = f'Сегодня {time['date_str']}, среда. \n\n1.\n<b>Математика</b>\n<u>8:30 - 10:05</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>\n\n2\n<b>Информатика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>\n\n3.\n<b>Литература</b>\n<u>12:20 - 13:55</u>\n<blockquote>309 аудитория\nДз: {get_homework('литература')}</blockquote>\n\n4\n<b>Обществознание</b>\n<u>14:10 - 15:45</u>\n<blockquote>424 аудитория\nДз: {get_homework('обществознание')}</blockquote>'

    tommorow_schedule_day_of_week_str = f'Завтра {time['date_tommorow_str']}, четверг. \n\n1.\n<b>Русский язык</b>\n<u>8:30 - 10:05</u>\n<blockquote>309 аудитория\nДз: {get_homework('русский')}</blockquote>\n\n2\n<b>Информатика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>\n\n3.\n<b>ОПД</b>\n<u>12:20 - 13:55</u>\n<blockquote>422 аудитория\nДз: {get_homework('опд')}</blockquote>\n\n4.\n<b>Математика</b>\n<u>14:10 - 15:45</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>'

elif time['day_of_week_str'] == 'Thursday':
    schedule_day_of_week_str = f'Сегодня {time['date_str']}, четверг. \n\n1.\n<b>Русский язык</b>\n<u>8:30 - 10:05</u>\n<blockquote>309 аудитория\nДз: {get_homework('русский')}</blockquote>\n\n2\n<b>Информатика</b>\n<u>10:15 - 11:50</u>\n<blockquote>404 аудитория\nДз: {get_homework('информатика')}</blockquote>\n\n3.\n<b>ОПД</b>\n<u>12:20 - 13:55</u>\n<blockquote>422 аудитория\nДз: {get_homework('опд')}</blockquote>\n\n4\n<b>Математика</b>\n<u>14:10 - 15:45</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>'

    tommorow_schedule_day_of_week_str = f'Завтра {time['date_tommorow_str']}, пятница!! \n\n1.\n<b>Физика</b>\n<u>8:30 - 10:05</u>\n<blockquote>404 аудитория\nДз: {get_homework('физика')}</blockquote>\n\n2\n<b>Биология</b>\n<u>10:15 - 11:50</u>\n<blockquote>119 аудитория\nДз: {get_homework('биология')}</blockquote>\n\n3.\n<b>Математика</b>\n<u>12:20 - 13:55</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>'

elif time['day_of_week_str'] == 'Friday':
    schedule_day_of_week_str = f'Сегодня {time['date_str']}, пятница!! \n\n1.\n<b>Физика</b>\n<u>8:30 - 10:05</u>\n<blockquote>404 аудитория\nДз: {get_homework('физика')}</blockquote>\n\n2\n<b>Биология</b>\n<u>10:15 - 11:50</u>\n<blockquote>119 аудитория\nДз: {get_homework('биология')}</blockquote>\n\n3.\n<b>Математика</b>\n<u>12:20 - 13:55</u>\n<blockquote>313 аудитория\nДз: {get_homework('математика')}</blockquote>'

    tommorow_schedule_day_of_week_str = f'Завтра суббота, выходной'

elif time['day_of_week_str'] == 'Saturday':
    schedule_day_of_week_str = 'Сегодня суббота, выходной'
    
    tommorow_schedule_day_of_week_str = 'чиллируем'

elif time['day_of_week_str'] == 'Sunday':
    schedule_day_of_week_str = 'завтра в шарагу 😨.'
    
    tommorow_schedule_day_of_week_str = f'Завтра {time['date_tommorow_str']}, понедельник. \n\n1.\n<b>История</b>\n<u>8:30 - 10:05</u>\n<blockquote>424 аудитория\nДз: {get_homework('история')}</blockquote>\n\n2\n<b>Физкультура</b>\n<u>10:15 - 11:50</u>\n<blockquote>Спортивный зал</blockquote>\n\n3.\n<b>Английский язык</b>\n<u>12:20 - 13:55</u>\n<blockquote>413 аудитория - 1 группа\nДз: {get_homework('англ1')}\n314 аудитория - 2 группа\nДз: {get_homework('англ2')}</blockquote>\n\n4.\n<b>Русский язык</b>\n<u>14:10 - 15:45</u>\n<blockquote>309 аудитория\nДз: {get_homework('русский')}</blockquote>'



@router.inline_query()
async def handle_inline_query(inline_query: types.InlineQuery):
    query_text = inline_query.query.lower()  # делаем все строчные для удобства
    result1 = InlineQueryResultArticle(
            id='Расписание',
            title='Расписание',
            description='хочется пары сегодняшние узнать...',
            input_message_content = InputTextMessageContent(
                message_text = schedule_day_of_week_str,
                parse_mode = 'HTML'
                )
            )
    result2 = InlineQueryResultArticle(
            id='Расписание на завтра',
            title='Расписание на завтра',
            description='интересно, какие завтра пары?..',
            input_message_content = InputTextMessageContent(
                message_text = tommorow_schedule_day_of_week_str,
                parse_mode = 'HTML'
                )
            )
    await inline_query.answer([result1, result2], cache_time=0)

