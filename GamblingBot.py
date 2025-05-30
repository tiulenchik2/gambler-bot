from os import getenv
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Dice

import CSVWork

logging.basicConfig(level=logging.INFO)
bot = Bot(token=getenv("GAMBLING_BOT_TOKEN"))
DATA_FILE = "test_users.csv"
VALUES = ["BAR", "Grapes", "Lemon", "7"]
dp = Dispatcher()

@dp.message()
async def check_rolls(message: types.Message):
    if isinstance(message.dice, Dice):
        rolled = message.dice
        dice_value = rolled.value
        
        dice_value -= 1
        result = []
        for _ in range(3):
            result.append(VALUES[dice_value % 4])
            dice_value //= 4
        await asyncio.sleep(3)
        if rolled.emoji == "🎰":
            if rolled.value == 64:
                pass # add soon score tracking
@dp.message(Command("add"))
async def add_user(message: types.Message):
    print(1)
    if CSVWork.is_user_exists(DATA_FILE, message.from_user.username):
        await message.reply(f"Ти вже у статистиці!")
    else:
        CSVWork.create_record(DATA_FILE, [message.from_user.username, 0, 0, 0])
        await message.reply(f"Записав тебе в свою пам'ять. Приємної гри!'")

@dp.message(Command("stats"))
async def check_stats(message: types.Message):
    await message.answer(str(CSVWork.read_records(DATA_FILE)))


async def main():
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())