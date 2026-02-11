import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_USER_ID, DB_PATH
from database import Database
from keyboards import (
    get_main_keyboard, get_tasks_keyboard, get_cancel_keyboard,
    get_calendar_keyboard, get_time_keyboard, get_task_actions_keyboard, get_back_keyboard
)
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("Установите переменную окружения TASKFLOW_BOT_TOKEN с токеном бота")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(DB_PATH)


# Состояния FSM
class AddTaskState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_manual_time = State()


# Временное хранилище данных
temp_data = {}


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я TaskFlow Scheduler Bot\n\n"
        "Управляй задачами через меню ☰ или кнопки ниже!",
        reply_markup=get_main_keyboard()
    )


# Команда /add
@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await btn_add(message, state)


# Команда /list
@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    await btn_all_tasks(message)


# Команда /today
@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    await btn_today(message)


# Команда /overdue
@dp.message(Command("overdue"))
async def cmd_overdue(message: types.Message):
    await btn_overdue(message)


# Команда /stats
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    await btn_stats(message)


# ➕ Добавить задачу
@dp.message(F.text == "➕ Добавить")
async def btn_add(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название задачи:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddTaskState.waiting_for_title)


# Название задачи
@dp.message(AddTaskState.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(title=message.text)
    await message.answer(
        "Введите описание:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddTaskState.waiting_for_description)


# Описание задачи
@dp.message(AddTaskState.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(description=message.text)
    await message.answer(
        "Выберите дату:",
        reply_markup=get_calendar_keyboard()
    )
    await state.set_state(AddTaskState.waiting_for_date)


# Выбор даты (inline callback)
@dp.callback_query(F.data.startswith("date_"))
async def process_date(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    year = int(data_parts[1])
    month = int(data_parts[2])
    day = int(data_parts[3])
    
    date = datetime(year, month, day)
    await state.update_data(date=date)
    
    await callback.message.edit_text(
        f"Выбрана дата: {day:02d}.{month:02d}.{year}\n\nВыберите время:",
        reply_markup=get_time_keyboard()
    )
    
    await state.set_state(AddTaskState.waiting_for_time)
    await callback.answer()


# Выбор времени (inline callback)
@dp.callback_query(F.data.startswith("time_"))
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.split("_")[1]
    
    if time_str == "manual":
        await callback.message.edit_text(
            "Введите время в формате ЧЧ:ММ (например, 14:30):"
        )
        await state.set_state(AddTaskState.waiting_for_manual_time)
        await callback.answer()
        return
    
    # Парсим время
    hour, minute = map(int, time_str.split(":"))
    
    # Получаем данные из состояния
    data = await state.get_data()
    date = data["date"]
    
    # Создаём дедлайн
    deadline = date.replace(hour=hour, minute=minute)
    
    # Создаём задачу
    task_id = db.create_task(
        title=data["title"],
        description=data["description"],
        deadline=deadline
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ Задача создана!\n\n"
        f"📋 {data['title']}\n"
        f"📝 {data['description']}\n"
        f"⏰ {deadline.strftime('%d.%m.%Y %H:%M')}"
    )
    
    await callback.message.answer(
        "Готово!",
        reply_markup=get_main_keyboard()
    )
    
    await callback.answer()


# Ввод времени вручную
@dp.message(AddTaskState.waiting_for_manual_time)
async def process_manual_time(message: types.Message, state: FSMContext):
    try:
        hour, minute = map(int, message.text.split(":"))
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError()
        
        # Получаем данные из состояния
        data = await state.get_data()
        date = data["date"]
        
        # Создаём дедлайн
        deadline = date.replace(hour=hour, minute=minute)
        
        # Создаём задачу
        task_id = db.create_task(
            title=data["title"],
            description=data["description"],
            deadline=deadline
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ Задача создана!\n\n"
            f"📋 {data['title']}\n"
            f"📝 {data['description']}\n"
            f"⏰ {deadline.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=get_main_keyboard()
        )
        
    except (ValueError, IndexError):
        await message.answer(
            "❌ Неверный формат. Введите время в формате ЧЧ:ММ (например, 14:30):"
        )


# Навигация по календарю
@dp.callback_query(F.data.startswith("cal_"))
async def process_calendar_navigation(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    year = int(data_parts[1])
    month = int(data_parts[2])
    
    # Корректируем месяц
    if month == 0:
        month = 12
        year -= 1
    elif month == 13:
        month = 1
        year += 1
    
    await callback.message.edit_reply_markup(
        reply_markup=get_calendar_keyboard(year, month)
    )
    await callback.answer()


# Игнорируемые callback
@dp.callback_query(F.data == "ignore")
async def process_ignore(callback: types.CallbackQuery):
    await callback.answer()


# Отмена
@dp.callback_query(F.data == "cancel")
async def process_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено")
    await callback.message.answer("Главное меню:", reply_markup=get_main_keyboard())
    await callback.answer()


# 📋 Задачи
@dp.message(F.text == "📋 Задачи")
async def btn_tasks(message: types.Message):
    await message.answer("Выберите:", reply_markup=get_tasks_keyboard())


# 📅 Сегодня
@dp.message(F.text == "📅 Сегодня")
async def btn_today(message: types.Message):
    tasks = db.get_today_tasks()
    
    if not tasks:
        await message.answer("На сегодня задач нет! ✅", reply_markup=get_main_keyboard())
        return
    
    text = "📅 Задачи на сегодня:\n\n"
    for task in tasks:
        status_emoji = {"pending": "⏳", "running": "▶️", "completed": "✅"}.get(task["status"], "❓")
        deadline_str = task["deadline"].split(".")[0]  # Убираем микросекунды
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        text += f"{status_emoji} [{task['id']}] {task['title']}\n"
        text += f"   ⏰ {deadline.strftime('%H:%M')}\n\n"
    
    await message.answer(text, reply_markup=get_main_keyboard())


# ⚠️ Просроченные
@dp.message(F.text == "⚠️ Просроченные")
async def btn_overdue(message: types.Message):
    tasks = db.get_overdue_tasks()
    
    if not tasks:
        await message.answer("Нет просроченных задач! ✅", reply_markup=get_main_keyboard())
        return
    
    text = "⚠️ Просроченные задачи:\n\n"
    for task in tasks:
        deadline_str = task["deadline"].split(".")[0]  # Убираем микросекунды
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        text += f"❌ [{task['id']}] {task['title']}\n"
        text += f"   ⏰ Было: {deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await message.answer(text, reply_markup=get_main_keyboard())


# 📋 Все задачи
@dp.message(F.text == "📋 Все задачи")
async def btn_all_tasks(message: types.Message):
    tasks = db.get_all_tasks()
    
    if not tasks:
        await message.answer("Активных задач нет! ✅", reply_markup=get_main_keyboard())
        return
    
    text = "📋 Все активные задачи:\n\n"
    for task in tasks[:20]:  # Показываем первые 20
        status_emoji = {"pending": "⏳", "running": "▶️", "completed": "✅"}.get(task["status"], "❓")
        deadline_str = task["deadline"].split(".")[0]  # Убираем микросекунды
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
        text += f"{status_emoji} [{task['id']}] {task['title']}\n"
        text += f"   ⏰ {deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    if len(tasks) > 20:
        text += f"... и ещё {len(tasks) - 20} задач"
    
    await message.answer(text, reply_markup=get_main_keyboard())


# 📊 Статистика
@dp.message(F.text == "📊 Статистика")
async def btn_stats(message: types.Message):
    stats = db.get_stats()
    
    text = "📊 Статистика:\n\n"
    text += f"📋 Всего задач: {stats['total']}\n"
    text += f"⏳ Ожидают: {stats['pending']}\n"
    text += f"▶️ В работе: {stats['running']}\n"
    text += f"✅ Выполнено: {stats['completed']}\n"
    text += f"⚠️ Просрочено: {stats['overdue']}"
    
    await message.answer(text, reply_markup=get_main_keyboard())


# 🔙 Назад
@dp.message(F.text == "🔙 Назад")
async def btn_back(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())


# ⚙️ Настройки (заглушка)
@dp.message(F.text == "⚙️ Настройки")
async def btn_settings(message: types.Message):
    await message.answer(
        "⚙️ Настройки в разработке\n\n"
        "Пока доступны только базовые функции",
        reply_markup=get_main_keyboard()
    )


# Обработка inline кнопок (done, start, delete)
@dp.callback_query(F.data.startswith("done_"))
async def process_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    
    if db.update_task_status(task_id, "completed"):
        await callback.message.edit_text("✅ Задача выполнена!")
    else:
        await callback.answer("❌ Задача не найдена")
    
    await callback.answer()


@dp.callback_query(F.data.startswith("start_"))
async def process_start(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    
    if db.update_task_status(task_id, "running"):
        await callback.message.edit_text("▶️ Задача в работе!")
    else:
        await callback.answer("❌ Задача не найдена")
    
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_"))
async def process_delete(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    
    if db.delete_task(task_id):
        await callback.message.edit_text("🗑 Задача удалена!")
    else:
        await callback.answer("❌ Задача не найдена")
    
    await callback.answer()


# Запуск бота
async def main():
    logger.info("Starting TaskFlow Scheduler Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
