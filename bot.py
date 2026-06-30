import json
import os
from datetime import datetime

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import F

from aiogram.filters import Command

from aiogram.types import Message
from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup

from dotenv import load_dotenv

from program import PROGRAM


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(TOKEN)

dp = Dispatcher()

DATA_FILE = "data.json"


MENU = ReplyKeyboardMarkup(

    keyboard=[

        [KeyboardButton(text="🏋️ Начать тренировку")],

        [KeyboardButton(text="📊 История")]

    ],

    resize_keyboard=True

)


def load_data():

    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf8") as f:
        return json.load(f)


def save_data(data):

    with open(DATA_FILE, "w", encoding="utf8") as f:

        json.dump(

            data,
            f,
            ensure_ascii=False,
            indent=4

        )


db = load_data()


def get_user(user_id):

    user_id = str(user_id)

    if user_id not in db:

        db[user_id] = {

            "history": [],

            "current": None

        }

    return db[user_id]


def current_plan(number):

    if number <= len(PROGRAM):

        return PROGRAM[number - 1]

    return PROGRAM[-1]


@dp.message(Command("start"))
async def start(message: Message):

    get_user(message.from_user.id)

    save_data(db)

    await message.answer(

        "Бот готов.",

        reply_markup=MENU

    )


@dp.message(F.text == "🏋️ Начать тренировку")
async def start_workout(message: Message):

    user = get_user(message.from_user.id)

    if user["current"] is not None:

        await show_next_set(message)

        return

    workout_number = len(user["history"]) + 1

    plan = current_plan(workout_number)

    user["current"] = {

        "number": workout_number,

        "date": datetime.now().strftime("%d.%m.%Y"),

        "exercise": "pullups",

        "set": 0,

        "plan": plan,

        "results": {

            "pullups": [],

            "dips": []

        }

    }

    save_data(db)

    await show_next_set(message)


async def show_next_set(message: Message):

    user = get_user(message.from_user.id)

    current = user["current"]

    exercise = current["exercise"]

    plan = current["plan"][exercise]

    index = current["set"]

    if index >= len(plan):

        if exercise == "pullups":

            current["exercise"] = "dips"

            current["set"] = 0

            save_data(db)

            await show_next_set(message)

            return

        await finish_workout(message)

        return

    planned = plan[index]

    text = "Подтягивания" if exercise == "pullups" else "Брусья"

    if planned == -1:

        target = "Максимум"

    else:

        target = str(planned)

    previous = None

    if len(user["history"]) > 0:

        last = user["history"][-1]

        if exercise in last["results"]:

            previous_sets = last["results"][exercise]

            if index < len(previous_sets):

                previous = previous_sets[index]

    msg = (
        f"🏋️ {text}\n\n"
        f"Подход {index + 1}/{len(plan)}\n"
    )

    if planned == -1:
        msg += "План: МАКСИМУМ\n"
    else:
        msg += f"План: {target}\n"

    if previous is not None:
        msg += f"Прошлый раз: {previous}\n"

    msg += "\nВведите количество повторений."

    await message.answer(msg)


@dp.message(F.text.regexp(r"^\d+$"))
async def save_result(message: Message):

    user = get_user(message.from_user.id)

    if user["current"] is None:
        return

    current = user["current"]

    exercise = current["exercise"]

    value = int(message.text)

    current["results"][exercise].append(value)

    current["set"] += 1

    save_data(db)

    await show_next_set(message)


async def finish_workout(message: Message):

    user = get_user(message.from_user.id)

    current = user["current"]

    user["history"].append(current)

    user["current"] = None

    save_data(db)

    pullups_total = sum(current["results"]["pullups"])
    dips_total = sum(current["results"]["dips"])

    text = (
        f"✅ Тренировка №{current['number']}\n"
        f"{current['date']}\n\n"
        f"Подтягивания: {pullups_total}\n"
        f"Брусья: {dips_total}"
    )

    if len(user["history"]) >= 2:

        prev = user["history"][-2]

        prev_pullups = sum(prev["results"]["pullups"])
        prev_dips = sum(prev["results"]["dips"])

        text += (
            f"\n\nΔ Подтягивания: {pullups_total - prev_pullups:+d}"
            f"\nΔ Брусья: {dips_total - prev_dips:+d}"
        )

    await message.answer(text, reply_markup=MENU)

@dp.message(F.text == "📊 История")
async def history(message: Message):

    user = get_user(message.from_user.id)

    if not user["history"]:

        await message.answer("История пуста.")

        return

    lines = []

    for workout in reversed(user["history"]):

        pullups = sum(workout["results"]["pullups"])

        dips = sum(workout["results"]["dips"])

        lines.append(

            "\n".join(

                [

                    f"№{workout['number']}",

                    workout["date"],

                    f"Подтягивания: {pullups}",

                    f"Брусья: {dips}",

                    "────────────"

                ]

            )

        )

    await message.answer(

        "\n".join(lines)

    )


@dp.message()
async def unknown(message: Message):

    if get_user(message.from_user.id)["current"] is not None:

        await message.answer(
            "Введите только число."
        )

        return

    await message.answer(
        "Используйте кнопки меню.",
        reply_markup=MENU
    )


async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":

    import asyncio

    asyncio.run(main())

