from os import getenv; from dotenv import load_dotenv
import asyncio
import logging
from aiogram import Bot, Router, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Dice
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode

import db_opers
from config import PENALTY, USERS_PER_PAGE, DELETION_DELAY, STATS_DELETION_DELAY, THREE_IN_A_ROW_WIN, SEVEN_WIN

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
        res += f"<b>{idx}</b>. {user[1]}: {user[6]} очок, {user[4]} круток ({user[5]} виграшні)\n"
    return res

@router.message(Command("stats"))
async def check_stats(message: types.Message):
    if db_opers.is_user_exists(message.from_user.id, message.chat.id):
        user_stats = db_opers.get_user(message.from_user.id)
        # (id, user_name, user_id, chat_id, spins, wins, score)
        user_place = db_opers.get_user_rank(message.from_user.id, message.chat.id)
        print(user_stats)
        await message.reply(
            f"<b>Стата користувача {user_stats[1]}</b>\n\n"
            f"<b>РАХУНОК: {user_stats[6]}</b>\n"
            f"Місце у рейтингу: {user_place}\n"
            f"<b>Всього круток: {user_stats[4]}</b>\n"
            f"З них виграшних: {user_stats[5]}\n",
        parse_mode=ParseMode.HTML)
    else:
        await message.reply("Не знайшов інфи по користувачу.")
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id, delay=STATS_DELETION_DELAY))
    asyncio.create_task(
            delete_message(chat_id=message.chat.id, message_id=message.message_id+1, delay=STATS_DELETION_DELAY))


@router.message(Command("stats_all"))
async def check_all_stats(message: types.Message):
    all_stats = db_opers.get_sorted_users_by_score(message.chat.id)
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
    all_stats = db_opers.get_sorted_users_by_score(query.message.chat.id)
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
    except TelegramBadRequest:
        pass
    await query.answer()
@router.message(Command("stats_top"))
async def check_all_stats(message: types.Message):
    all_stats = db_opers.get_sorted_users_by_score(message.chat.id)
    TOP_VALUE = len(all_stats) if len(all_stats) < 10 else 10
    res = f'<b>ТОП-{TOP_VALUE} ГЕМБЛЕРІВ ЧАТІКА:</b>\n'
    for a in range(TOP_VALUE):
        res += f"<b>{a+1}</b>. {all_stats[a][1]}: {all_stats[a][6]} очок, {all_stats[a][4]} круток ({all_stats[a][5]} виграшні)\n"
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
        if not db_opers.get_user(message.from_user.id):
            db_opers.add_user(user_name, message.from_user.id, message.chat.id) 
            await message.reply("Вітання у грі, автоматично зареєстрував.\nДля детальної інформації - /info")
        
        if message.forward_date:
            await message.reply("Шахраям даємо по шапці. -100 з рахунку.")
            db_opers.update_score(message.from_user.id, -PENALTY)
        else:
            rolled = message.dice
            # Оновлюємо загальну кількість круток
            db_opers.update_rolls_total(message.from_user.id)
            
            if rolled.emoji == "🎰":
                if rolled.value == 64:  # 777
                    db_opers.update_score(message.from_user.id, SEVEN_WIN)
                    db_opers.update_rolls_win(message.from_user.id)
                elif rolled.value in (1, 22, 43):  # три в ряд
                    db_opers.update_score(message.from_user.id, THREE_IN_A_ROW_WIN)
                    db_opers.update_rolls_win(message.from_user.id)
                else:  # програш
                    db_opers.update_score(message.from_user.id, -1)
        
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