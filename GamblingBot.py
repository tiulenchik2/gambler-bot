from os import getenv
import asyncio
import logging
from aiogram import Bot, Router, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Dice
from aiogram.exceptions import TelegramBadRequest
from pydantic_core.core_schema import field_after_validator_function

import CSVWork

logging.basicConfig(level=logging.INFO)
bot = Bot(token=getenv("GAMBLING_BOT_TOKEN"))
DATA_FILE = "test_users.csv"
VALUES = ["BAR", "Grapes", "Lemon", "7"]
router = Router()
dp = Dispatcher(); dp.include_router(router)

@router.message(Command("stats"))
async def check_stats(message: types.Message):
    if CSVWork.is_user_exists(DATA_FILE, message.from_user.id, message.chat.id):
        user_stats = CSVWork.return_user_record(DATA_FILE, message.from_user.id, message.chat.id)
        await message.reply(f"Стата користувача {user_stats[0]}\n"
        f"РАХУНОК: {user_stats[3]}\n\nВсього круток: {user_stats[1]}\nЗ них виграшних: {user_stats[2]}\n")
    else:
        await message.reply("Не знайшов інфи по користувачу.")

@router.message(Command("stats_all"))
async def check_all_stats(message: types.Message):
    all_stats = CSVWork.sort_records(DATA_FILE, message.chat.id, 3)
    res = 'ВСЯ СТАТА ГЕМБЛЕРІВ ЧАТІКА:\n'
    for a in range(len(all_stats)):
        res += f"{a+1}. {all_stats[a][0]}: {all_stats[a][3]} очок, {all_stats[a][1]} круток ({all_stats[a][2]} виграшні)\n"
    await message.reply(res)
@router.message(Command("stats_top"))
async def check_all_stats(message: types.Message):
    all_stats = CSVWork.sort_records(DATA_FILE, message.chat.id, 3)
    TOP_VALUE = len(all_stats) if len(all_stats) < 10 else 10
    res = f'ТОП-{TOP_VALUE} ГЕМБЛЕРІВ ЧАТІКА:\n'
    for a in range(TOP_VALUE):
        res += f"{a+1}. {all_stats[a][0]}: {all_stats[a][3]} очок, {all_stats[a][1]} круток ({all_stats[a][2]} виграшні)\n"
    await message.reply(res)

@router.message(Command("info"))
async def announce_info(message: types.Message):
    await message.reply("Правила до біса прості:\n- кидаєш смайлик слота - ти у статистиці."
                        "\n- кожна крутка коштує 1 очко\n- за три в ряд нараховується +25 очок\n- за 777 нараховується +50"
                        "\n- /stats виводить твою інфу: рахунок, скільки крутанув, скільки виграв.\n"
                        "- /stats_all - вся статистика чату.\n"
                        "- /stats_top - лише топ чату\n\nЩиро вдячний, ваш девелопер <3")

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
            user_stat[3] = str(int(user_stat[3]) - 100)
        else:
            rolled = message.dice
            user_stat[1] = str(int(user_stat[1]) + 1)
            if rolled.emoji == "🎰":
                if rolled.value == 64:
                    user_stat[3] = str(int(user_stat[3]) + 50)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                elif rolled.value in (1, 22, 43):
                    user_stat[3] = str(int(user_stat[3]) + 25)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                else:
                    user_stat[3] = str(int(user_stat[3]) - 1)
        CSVWork.update_record(DATA_FILE, message.from_user.id, message.chat.id, user_stat)
        asyncio.create_task(
            delete_dice(chat_id=message.chat.id, message_id=message.message_id, delay=7.0))
       
async def delete_dice(chat_id: int, message_id: int, delay: float):
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