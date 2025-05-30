from os import getenv
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Dice

logging.basicConfig(level=logging.INFO)
bot = Bot(token=getenv("GAMBLING_BOT_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def command_start(message: types.Message):
    await message.answer("Hello!")


async def main():
    await dp.start_polling(bot)
@dp.message()
async def check_rolls(message: types.Message):
    if isinstance(message.dice, Dice):
        rolled = message.dice
        dice_value = rolled.value
        VALUES = ["BAR", "Grapes", "Lemon", "7"]
        dice_value -= 1
        result = []
        for _ in range(3):
            result.append(VALUES[dice_value % 4])
            dice_value //= 4
        await asyncio.sleep(3)
        await message.answer(f"I see {rolled.emoji}. And you rolled {rolled.value}")
        if rolled.emoji == "🎰":
            await message.answer(f"Slot machine! {result[0]}, {result[1]}, {result[2]}")
if __name__ == "__main__":
    asyncio.run(main())