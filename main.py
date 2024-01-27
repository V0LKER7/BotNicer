from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import logging
import asyncio
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import psycopg
from aiogram.filters import CommandStart, Command
from datetime import datetime
from aiogram.types import BotCommand, BotCommandScopeDefault
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import time
BOT_TOKEN = '6785002507:AAEVPYCeB_GLYQ8SOqMMBAqXCDUn7nVQhGM'
conn = psycopg.connect("dbname=tgnotify user=postgres password=123")
def reply_keyboard():
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.button(text='🎯Меню')
    keyboard_builder.button(text='🔔Создать напоминие')
    keyboard_builder.button(text='📝Список напоминаний')
    keyboard_builder.button(text='🗑️Удалить напоминание')
    keyboard_builder.adjust(2)
    return keyboard_builder.as_markup(resize_keyboard=True, one_time_keyboard=False, selective=True)
class StepsForm(StatesGroup):
    GET_NOTICE = State()
    DEL_NOTICE = State()
async def menu_button(message: Message):
    await message.answer('Привет, друг! 👋 Я - твой личный телеграмм-бот с напоминаниями, и я здесь, чтобы помочь тебе не забывать о важных вещах! 📝\n\n\
Мои возможности:\n\n\
📅 Добавление напоминания: Просто отправь мне сообщение с текстом напоминания и датой, когда ты хочешь, чтобы оно появилось. Я помню все!\n\n\
📝 Все напоминания: Если тебе нужно проверить свой список напоминаний, просто напиши мне "Показать все напоминания", и я передам тебе список.\n\n\
🗑️ Удаление напоминания: Если ты решил, что напоминание уже не нужно, просто укажи мне номер напоминания, которое ты хочешь удалить, и я сделаю это.!!',reply_markup=reply_keyboard())
async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description = 'начало работы'
        ),
        BotCommand(
            command="menu",
            description = 'перейти в меню'
        ),
        BotCommand(
            command="addnotice",
            description='добавить напоминание'
        ),
        BotCommand(
            command="list",
            description='открыть список напоминаний'
        ),
        BotCommand(
            command="delete",
            description='удалить напоминание'
        ),
        ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
async def on_startup(bot: Bot):
    await set_commands(bot)
async def notice_me(bot: Bot):
    cur = conn.execute("SELECT telegramid, datetime, name FROM schedule")
    data0 = cur.fetchall()
    u = len(data0)
    for i in range(0, u):
        data = data0[i]
        tg_id = data[0]
        date = data[1]
        text = data[2]
        if date.date() == datetime.now().date():
            await bot.send_message(chat_id=tg_id, text=text)
async def welcome_message(message: Message):
    await message.answer('Привет, друг! 👋 Я - твой личный телеграмм-бот с напоминаниями, и я здесь, чтобы помочь тебе не забывать о важных вещах! 📝\n\n\
Мои возможности:\n\n\
📅 Добавление напоминания: Просто отправь мне сообщение с текстом напоминания и датой, когда ты хочешь, чтобы оно появилось. Я помню все!\n\n\
📝 Все напоминания: Если тебе нужно проверить свой список напоминаний, просто напиши мне "Показать все напоминания", и я передам тебе список.\n\n\
🗑️ Удаление напоминания: Если ты решил, что напоминание уже не нужно, просто укажи мне номер напоминания, которое ты хочешь удалить, и я сделаю это.!!', reply_markup=reply_keyboard())

async def create_notice(message: Message, state: FSMContext):
    await message.answer('Просто отправь мне сообщение с датой и текстом напоминания (день.месяц.год текст), когда ты хочешь, чтобы оно появилось. Я помню все!')
    await state.set_state(StepsForm.GET_NOTICE)
async def continue_creating(message: Message, state: FSMContext):
    tgid = message.from_user.id
    text = message.text.split(' ', 1)[-1]
    dateString = message.text.split(' ', 1)[0]
    date = datetime.strptime(dateString, '%d.%m.%Y')
    cur = conn.execute("INSERT INTO schedule (telegramid, datetime, name) VALUES (%s, %s, %s)", (tgid, date, text))
    await message.answer('Напоминание успешно создано, вы можете увидеть его в списке своих напоминаний!')
    await state.clear()
    conn.commit()
# async def finish_creating(message: Message, state:)
#     data = '05 Dec 2000'
#     cur = conn.cursor("INSERT INTO SCHEDULE (datetime) VALUES (%s) to_timestamp(data, 'DD Mon YYYY')")
#     conn.commit()
async def delete_notice(message: Message, state: FSMContext):
    cur = conn.execute('SELECT * FROM schedule WHERE telegramid =%s', (message.from_user.id,))
    data1 = cur.fetchone()
    if data1 is None:
        await message.answer(
            'Простите у вас пока, что нету напоминаний! Но вы в любое время можете создать их, выбрав нужный пункт в меню!')
        return
    cur = conn.execute("SELECT id, datetime, name FROM schedule WHERE telegramid =%s", (message.from_user.id,))
    data0 = cur.fetchall()
    u = len(data0)
    text = f'👋 Вот список ваших напоминаний в формате id,date,text: \n'
    for i in range(0, u):
        data = data0[i]
        id = data[0]
        date = data[1]
        name = data[2]
        text1 = f'{text}\n{id} | {date.date()} | {name}'
        text = text1
    await message.answer(
        f'{text1} \n\nНапишите мне дату, которую вы хотите удалить!')
    text1 = str()
    text = str()
    await state.set_state(StepsForm.DEL_NOTICE)

async def continue_deletion(message: Message, state: FSMContext):
    cur = conn.execute('DELETE FROM schedule WHERE id =%s', (message.text,))
    await message.answer('Напоминание успешно удалено')
    conn.commit()
    await state.clear()
async def get_notices(message: Message):
    cur = conn.execute('SELECT * FROM schedule WHERE telegramid =%s', (message.from_user.id,))
    data1 = cur.fetchone()
    if data1 is None:
        await message.answer('Простите у вас пока, что нету напоминаний! Но вы в любое время можете создать их, выбрав нужный пункт в меню!')
        return
    cur = conn.execute("SELECT id, datetime, name FROM schedule WHERE telegramid =%s", (message.from_user.id,))
    data0 = cur.fetchall()
    u = len(data0)
    text = f'Здравствуйте, {message.from_user.first_name}! 👋 Вот список ваших напоминаний в формате id,date,text: \n'
    for i in range(0, u):
        data=data0[i]
        id = data[0]
        date = data[1]
        name = data[2]
        dateString = date.strftime('%d.%m.%Y')
        text1 = f'{text}\n{id} | {dateString} | {name}'
        text = text1
    await message.answer(f'{text1} \n\nЕсли вам нужно удалить какое-то напоминание, просто выберите нужный пункт в меню. Я всегда готов помочь! 🤖 ')
    text1=str()
    text=str()
async def start():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    bot = Bot(token=BOT_TOKEN)
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(notice_me, trigger='cron', hour='*',
                    start_date=datetime.now(), kwargs={'bot': bot})
    scheduler.start()

    dp = Dispatcher()
    dp.message.register(welcome_message, CommandStart())
    dp.startup.register(on_startup)
    dp.message.register(get_notices, F.text == '📝Список напоминаний')
    dp.message.register(get_notices, Command(commands='list'))
    dp.message.register(menu_button, F.text == '🎯Меню')
    dp.message.register(menu_button, Command(commands='menu'))
    dp.message.register(create_notice, F.text == '🔔Создать напоминие')
    dp.message.register(create_notice, Command(commands="addnotice"))
    dp.message.register(continue_creating, StepsForm.GET_NOTICE)
    dp.message.register(delete_notice, F.text == '🗑️Удалить напоминание')
    dp.message.register(delete_notice, Command(commands="deletenotice"))
    dp.message.register(continue_deletion, StepsForm.DEL_NOTICE)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
