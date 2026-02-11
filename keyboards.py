from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import calendar


def get_main_keyboard():
    """Главное меню"""
    kb = [
        [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="📋 Задачи")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=False)


def get_tasks_keyboard():
    """Меню задач"""
    kb = [
        [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="⚠️ Просроченные")],
        [KeyboardButton(text="📋 Все задачи"), KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_task_actions_keyboard(task_id: int):
    """Действия с задачей"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Выполнить", callback_data=f"done_{task_id}"),
        InlineKeyboardButton(text="▶️ В работу", callback_data=f"start_{task_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{task_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    
    return builder.as_markup()


def get_cancel_keyboard():
    """Кнопка отмены"""
    kb = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_calendar_keyboard(year: int = None, month: int = None):
    """Inline календарь"""
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    builder = InlineKeyboardBuilder()
    
    # Заголовок с месяцем и годом
    month_name = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    
    # Навигация по месяцам
    builder.row(
        InlineKeyboardButton(text="◀️", callback_data=f"cal_{year}_{month-1}"),
        InlineKeyboardButton(text=f"{month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal_{year}_{month+1}")
    )
    
    # Дни недели
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    builder.row(*[InlineKeyboardButton(text=day, callback_data="ignore") for day in days])
    
    # Дни месяца
    cal = calendar.Calendar(firstweekday=0)  # Понедельник первый
    
    today = datetime.now()
    
    for week in cal.monthdayscalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date = datetime(year, month, day)
                
                # Блокируем прошедшие дни
                if date.date() < today.date():
                    row.append(InlineKeyboardButton(text="·", callback_data="ignore"))
                elif date.date() == today.date():
                    # Подсвечиваем сегодняшний день
                    row.append(InlineKeyboardButton(text=f"•{day}•", callback_data=f"date_{year}_{month}_{day}"))
                else:
                    row.append(InlineKeyboardButton(text=str(day), callback_data=f"date_{year}_{month}_{day}"))
        
        builder.row(*row)
    
    # Быстрый выбор
    builder.row(
        InlineKeyboardButton(text="Сегодня", callback_data=f"date_{today.year}_{today.month}_{today.day}"),
        InlineKeyboardButton(text="Завтра", callback_data=f"date_{(today + timedelta(days=1)).year}_{(today + timedelta(days=1)).month}_{(today + timedelta(days=1)).day}"),
        InlineKeyboardButton(text="Через неделю", callback_data=f"date_{(today + timedelta(days=7)).year}_{(today + timedelta(days=7)).month}_{(today + timedelta(days=7)).day}")
    )
    
    return builder.as_markup()


def get_time_keyboard():
    """Inline выбор времени"""
    builder = InlineKeyboardBuilder()
    
    times = [
        ["09:00", "10:00", "11:00"],
        ["12:00", "13:00", "14:00"],
        ["15:00", "16:00", "17:00"],
        ["18:00", "19:00", "20:00"]
    ]
    
    for row in times:
        builder.row(*[InlineKeyboardButton(text=t, callback_data=f"time_{t}") for t in row])
    
    builder.row(InlineKeyboardButton(text="Вручную", callback_data="time_manual"))
    
    return builder.as_markup()


def get_back_keyboard():
    """Кнопка назад"""
    kb = [[KeyboardButton(text="🔙 Назад")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
