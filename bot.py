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

WORKOUT_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏹ Завершить тренировку")]
    ],
    resize_keyboard=True
)

CONFIRM_STOP_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Да"),
            KeyboardButton(text="⬅ Продолжить")
        ]
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

    user["current"] = None
    
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
        },
        "status": "IN_PROGRESS",
        "confirm_stop": False
    }

    save_data(db)

    await show_next_set(message)


async def show_next_set(message: Message):

    await message.answer(
        text,
        reply_markup=WORKOUT_MENU
    )

    @dp.message(F.text == "⏹ Завершить тренировку")

async def ask_stop(message: Message):

    user = get_user(message.from_user.id)

    if user["current"] is None:
        return

    user["current"]["confirm_stop"] = False
    save_data(db)

    await show_next_set(message)

    @dp.message(F.text == "✅ Да")
async def stop_training(message: Message):

    user = get_user(message.from_user.id)

    if user["current"] is None:
        return

    current = user["current"]

    if not current.get("confirm_stop"):
        return

    current["confirm_stop"] = False
    current["status"] = "INTERRUPTED"

    fill_remaining(current)

    await finish_workout(message)

    user = get_user(message.from_user.id)

    if user["current"] is None:
        return

    user["current"]["confirm_stop"] = True
    save_data(db)

    await message.answer(
        "Завершить тренировку?\n\n"
        "Все оставшиеся подходы будут автоматически сохранены значением 0.",
        reply_markup=CONFIRM_STOP_MENU
    )

    @dp.message(F.text == "⬅ Продолжить")
async def continue_training(message: Message):

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

    await message.answer(
        msg,
        reply_markup=WORKOUT_MENU
    )

@dp.message(F.text.regexp(r"^\d+$"))
async def save_result(message: Message):

    user = get_user(message.from_user.id)

    if user["current"] is None:
    return

    if user["current"].get("confirm_stop"):
    await message.answer(
        "Подтвердите завершение тренировки или продолжите тренировку.",
        reply_markup=CONFIRM_STOP_MENU
    )
    return

    current = user["current"]

    exercise = current["exercise"]

    value = int(message.text)

    current["results"][exercise].append(value)

    current["set"] += 1

    save_data(db)

    await show_next_set(message)

    def fill_remaining(current):

        exercise = current["exercise"]

        current_set = current["set"]

        # Если остановились на подтягиваниях —
        # дополняем оставшиеся подтягивания
        if exercise == "pullups":

            pull_plan = current["plan"]["pullups"]

            while len(current["results"]["pullups"]) < len(pull_plan):
                current["results"]["pullups"].append(0)

            # и полностью заполняем брусья
            dip_plan = current["plan"]["dips"]

            while len(current["results"]["dips"]) < len(dip_plan):
                current["results"]["dips"].append(0)

        # Если остановились уже на брусьях —
        # подтягивания не трогаем
        else:

            dip_plan = current["plan"]["dips"]

            while len(current["results"]["dips"]) < len(dip_plan):
                current["results"]["dips"].append(0)

async def finish_workout(message: Message):

    user = get_user(message.from_user.id)
    current = user["current"]

    if current.get("status") == "IN_PROGRESS":
        current["status"] = "COMPLETED"

    current["finish_date"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    user["history"].append(current)
    user["current"] = None

    save_data(db)

    pull_plan = current["plan"]["pullups"]
    dip_plan = current["plan"]["dips"]

    pull_fact = current["results"]["pullups"]
    dip_fact = current["results"]["dips"]

    pull_plan_total = sum(x for x in pull_plan if x != -1)
    dip_plan_total = sum(x for x in dip_plan if x != -1)

    pull_fact_total = sum(pull_fact)
    dip_fact_total = sum(dip_fact)

    completed_sets = sum(
        1
        for x in pull_fact + dip_fact
        if x > 0
    )

    skipped_sets = sum(
        1
        for x in pull_fact + dip_fact
        if x == 0
    )

    status = (
        "✅ Завершена"
        if current["status"] == "COMPLETED"
        else "⏹ Прервана"
    )

    text = (
        f"🏋️ Тренировка №{current['number']}\n"
        f"{current['date']}\n\n"

        f"Подтягивания\n"
        f"План: {pull_plan_total}\n"
        f"Факт: {pull_fact_total}\n\n"

        f"Брусья\n"
        f"План: {dip_plan_total}\n"
        f"Факт: {dip_fact_total}\n\n"

        f"Выполнено подходов: {completed_sets}\n"
        f"Пропущено подходов: {skipped_sets}\n\n"

        f"Статус: {status}"
    )

    if len(user["history"]) >= 2:

        prev = user["history"][-2]

        prev_pull = sum(prev["results"]["pullups"])
        prev_dips = sum(prev["results"]["dips"])

        text += (
            f"\n\n"
            f"Δ Подтягивания: {pull_fact_total - prev_pull:+d}\n"
            f"Δ Брусья: {dip_fact_total - prev_dips:+d}"
        )

    await message.answer(
        text,
        reply_markup=MENU
    )

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

        status = workout.get("status") or "COMPLETED"

        status_text = (
            "✅ Завершена"
            if status == "COMPLETED"
            else "⏹ Прервана"
        )

        lines.append(
            "\n".join(
                [
                    f"№{workout['number']}",
                    workout["date"],
                    status_text,
                    f"Подтягивания: {sum(workout['results']['pullups'])}",
                    f"Брусья: {sum(workout['results']['dips'])}",
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

