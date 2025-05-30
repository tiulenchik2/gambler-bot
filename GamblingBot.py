from os import getenv
import asyncio
import logging
from aiogram import Bot, Router, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.types import Dice

import CSVWork

logging.basicConfig(level=logging.INFO)
bot = Bot(token=getenv("GAMBLING_BOT_TOKEN"))
DATA_FILE = "test_users.csv"
VALUES = ["BAR", "Grapes", "Lemon", "7"]
CHAT_ID = -1002196221968
router = Router()
dp = Dispatcher(); dp.include_router(router)

@router.message(Command("add"), F.chat.id == CHAT_ID)
async def add_user(message: types.Message):
    logging.info("Add command received in group")
    if CSVWork.is_user_exists(DATA_FILE, message.from_user.username):
        await message.reply(f"Ти вже у статистиці!")
    else:
        CSVWork.create_record(DATA_FILE, [message.from_user.username, 0, 0, 0])
        await message.reply(f"Записав тебе в свою пам'ять. Приємної гри!")

@router.message(Command("stats"), F.chat.id == CHAT_ID)
async def check_stats(message: types.Message):
    logging.info("Stats command received")
    if CSVWork.is_user_exists(DATA_FILE, message.from_user.username):
        user_stats = CSVWork.return_user_record(DATA_FILE, message.from_user.username)
        await message.reply(f"Стата користувача @{message.from_user.username}\n"
        f"РАХУНОК: {user_stats[3]}\n\nВсього круток: {user_stats[1]}\nЗ них виграшних: {user_stats[2]}\n")
    else:
        await message.reply("Не знайшов інфи по користувачу. Можливо, зарєгаєшся?)\n(підказка: введи /add для того, аби потрапити в рейтинг)")

@router.message(Command("stats_all"), F.chat.id == CHAT_ID)
async def check_all_stats(message: types.Message):
    all_stats = CSVWork.sort_records(DATA_FILE, 3)
    res = 'ТОП ГЕМБЛЕРІВ ЧАТІКА:\n'
    for a in range(len(all_stats)):
        res += f"{a+1}. {all_stats[a][0]}: {all_stats[a][3]} очок, {all_stats[a][1]} круток ({all_stats[a][2]} виграшні)\n"
    await message.reply(res)

@router.message(Command("info"), F.chat.id == CHAT_ID)
async def announce_info(message: types.Message):
    await message.reply("Правила до біса прості:\n- кидаєш смайлик слота або пишеш /add (що, скоро, буде вже видалено)."
                        "\n- кожна крутка коштує 1 очко\n- за три в ряд нараховується +25 очок\n- за 777 нараховується +50"
                        "\n/stats виводить твою інфу, а /stats_all - топ чату.\nЩиро вдячний, ваш девелопер <3")

@router.message(F.chat.id == CHAT_ID)
async def check_rolls(message: types.Message):
    if isinstance(message.dice, Dice):
        if not CSVWork.is_user_exists(DATA_FILE, message.from_user.username):
            CSVWork.create_record(DATA_FILE, [message.from_user.username, -1, 0, 1])
            await message.reply("Вітання у грі, автоматично зареєстрував.")
        else:
            pass
        user_stat = CSVWork.return_user_record(DATA_FILE, message.from_user.username)
        if message.forward_date:
            await message.reply("Шахраям даємо по шапці. -100 з рахунку.")
            user_stat[3] = str(int(user_stat[3]) - 100)
        else:
            logging.info("Roll began")
            rolled = message.dice
            dice_value = rolled.value
            dice_value -= 1
            result = []
            for _ in range(3):
                result.append(VALUES[dice_value % 4])
                dice_value //= 4
            user_stat[1] = str(int(user_stat[1]) + 1)
            if rolled.emoji == "🎰":
                if rolled.value == 64:
                    user_stat[3] = str(int(user_stat[3]) + 50)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                    asyncio.sleep(2.7)
                    await message.reply("ГООООЛ! ТРИ ТОПОРА!!!")
                elif rolled.value in (1, 22, 43):
                    user_stat[3] = str(int(user_stat[3]) + 25)
                    user_stat[2] = str(int(user_stat[2]) + 1)
                    asyncio.sleep(2.7)
                    await message.reply("Гоооол! Три в ряд!")
                else:
                    user_stat[3] = str(int(user_stat[3]) - 1)
        CSVWork.update_record(DATA_FILE, message.from_user.username, user_stat)
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())