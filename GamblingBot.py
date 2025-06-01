from os import getenv; from dotenv import load_dotenv
import asyncio
import logging
from aiogram import Bot, Router, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Dice
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

import CSVWork
from config import DATA_FILE, PENALTY, USERS_PER_PAGE, DELETION_DELAY, STATS_DELETION_DELAY, THREE_IN_A_ROW_WIN, SEVEN_WIN

logging.basicConfig(level=logging.INFO)
load_dotenv(); bot = Bot(token=getenv("TEST_BOT_TOKEN"))
CHAT_INDICES = {}
router = Router()
dp = Dispatcher(); dp.include_router(router)

def get_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="<-", callback_data="prev")
    builder.button(text="->", callback_data="next")
    return builder.as_markup()

def get_stats_page(all_stats, page):
    total_pages = max((len(all_stats) - 1) // USERS_PER_PAGE + 1, 1)
    res = f'<b>ВСЯ СТАТА ГЕМБЛЕРІВ ЧАТІКА:</b>\n<i>Сторінка {page + 1} з {total_pages}</i>\n\n'
    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    for idx, user in enumerate(all_stats[start:end], start=start + 1):
        res += f"<b>{idx}</b>. {user[0]}: {user[3]} очок, {user[1]} круток ({user[2]} виграшні)\n"
    return res

@router.message(Command("stats"))
async def check_stats(message: types.Message):
    if CSVWork.is_user_exists(DATA_FILE, message.from_user.id, message.chat.id):
        user_stats = CSVWork.return_user_record(DATA_FILE, message.from_user.id, message.chat.id)
        all_stats = CSVWork.sort_records(DATA_FILE, message.chat.id, 3)
        user_place = None
        for idx, user in enumerate(all_stats):
            if str(user[4]) == str(message.from_user.id):
                user_place = idx + 1
                break
        await message.reply(
            f"<b>Стата користувача {user_stats[0]}</b>\n\n"
            f"<b>РАХУНОК: {user_stats[3]}</b>\n"
            f"Місце у рейтингу: {user_place}\n"
            f"<b>Всього круток: {user_stats[1]}</b>\n"
            f"З них виграшних: {user_stats[2]}\n",
        parse_mode=ParseMode.HTML)
    else:
        await message.reply("Не знайшов інфи по користувачу.")
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=STATS_DELETION_DELAY))
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id+1, delay=STATS_DELETION_DELAY))

@router.message(Command("stats_all"))
async def check_all_stats(message: types.Message):
    all_stats = CSVWork.sort_records(DATA_FILE, message.chat.id, 3)
    user_id = message.from_user.id
    CHAT_INDICES[user_id] = 0
    text = get_stats_page(all_stats, 0)
    await message.answer(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=STATS_DELETION_DELAY))
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id+1, delay=STATS_DELETION_DELAY))

@router.callback_query(F.data.in_(["prev", "next"]))
async def paginate_stats(query: types.CallbackQuery):
    user_id = query.from_user.id
    all_stats = CSVWork.sort_records(DATA_FILE, query.message.chat.id, 3)
    max_page = max((len(all_stats) - 1) // USERS_PER_PAGE, 0)
    page = CHAT_INDICES.get(user_id, 0)

    if query.data == "next":
        page = min(page + 1, max_page)
    elif query.data == "prev":
        page = max(page - 1, 0)

    CHAT_INDICES[user_id] = page
    text = get_stats_page(all_stats, page)
    try:
        await query.message.edit_text(text, reply_markup=get_keyboard(), parse_mode=ParseMode.HTML)
    except TelegramRetryAfter as e:
        await query.answer(f"Забагато запитів! Спробуй через {e.retry_after} сек.", show_alert=True)
        return
    except TelegramBadRequest:
        pass
    else:
        await query.answer()
@router.message(Command("stats_top"))
async def check_all_stats(message: types.Message):
    all_stats = CSVWork.sort_records(DATA_FILE, message.chat.id, 3)
    TOP_VALUE = len(all_stats) if len(all_stats) < 10 else 10
    res = f'<b>ТОП-{TOP_VALUE} ГЕМБЛЕРІВ ЧАТІКА:</b>\n'
    for a in range(TOP_VALUE):
        res += f"<b>{a+1}</b>. {all_stats[a][0]}: {all_stats[a][3]} очок, {all_stats[a][1]} круток ({all_stats[a][2]} виграшні)\n"
    await message.reply(res, parse_mode=ParseMode.HTML)
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=STATS_DELETION_DELAY))
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id+1, delay=STATS_DELETION_DELAY))

@router.message(Command("info"))
async def announce_info(message: types.Message):
    await message.reply("Правила до біса прості:\n- кидаєш смайлик слота - ти у статистиці."
                        "\n- кожна крутка коштує 1 очко\n- за три в ряд нараховується +25 очок\n- за 777 нараховується +50"
                        "\n- /stats виводить твою інфу: рахунок, скільки крутанув, скільки виграв.\n"
                        "- /stats_all - вся статистика чату.\n"
                        "- /stats_top - лише топ чату\n\nЩиро вдячний, ваш девелопер <3")
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=STATS_DELETION_DELAY))
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id+1, delay=STATS_DELETION_DELAY))

@router.message()
async def check_rolls(message: types.Message):
    if isinstance(message.dice, Dice):
        user_name = message.from_user.username if message.from_user.username != None else message.from_user.first_name
        if not CSVWork.is_user_exists(DATA_FILE, message.from_user.id, message.chat.id):
            CSVWork.create_record(DATA_FILE, [user_name, 0, 0, 0, message.from_user.id, message.chat.id])  
            await message.reply("Вітання у грі, автоматично зареєстрував.\nДля детальної інформації - /info")
        else:
            pass
        user_stat = CSVWork.return_user_record(DATA_FILE, message.from_user.id, message.chat.id)
        if message.forward_date:
            await message.reply("Шахраям даємо по шапці. -100 з рахунку.")
            user_stat[3] = str(int(user_stat[3]) - PENALTY)
        else:
            rolled = message.dice
            user_stat[1] = str(int(user_stat[1]) + 1)
            if rolled.emoji == "🎰":
                if rolled.value == 64:
                    user_stat[3] = str(int(user_stat[3]) + SEVEN_WIN)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                elif rolled.value in (1, 22, 43):
                    user_stat[3] = str(int(user_stat[3]) + THREE_IN_A_ROW_WIN)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                else:
                    user_stat[3] = str(int(user_stat[3]) - 1)
        CSVWork.update_record(DATA_FILE, message.from_user.id, message.chat.id, user_stat)
        asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=DELETION_DELAY))
       
async def delete_message(chat_id: int, message_id: int, delay: float):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())