import telebot
import psycopg2
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

# Укажите токен вашего Telegram-бота
API_TOKEN = ''

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "root",
    "host": "localhost",
    "port": 5432
}

bot = telebot.TeleBot(API_TOKEN)

DAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for day in DAYS:
    keyboard.add(KeyboardButton(day.capitalize()))
keyboard.add(KeyboardButton("Расписание текущей недели"))
keyboard.add(KeyboardButton("Расписание следующей недели"))

def get_full_schedule_for_day(day, week_type):
    query = """
    SELECT t.time, t.room_numb, t.subject, te.full_name
    FROM timetable t
    LEFT JOIN teacher te ON t.subject = te.subject
    WHERE LOWER(t.day) = LOWER(%s) AND (t.week = %s OR t.week = 'Общая')
    ORDER BY t.time;
    """
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print(f"Запрос: {day}, {week_type}")  # Логируем запрос
        cursor.execute(query, (day, week_type))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        print(f"Результаты: {rows}")  # Лог результатов
        return rows
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных или выполнения запроса:\n{e}")
        return []

def get_schedule_for_week(week_offset):
    current_date = datetime.now()
    if week_offset == 0:  # Текущая неделя
        start_date = current_date - timedelta(days=current_date.weekday())
        week_type = 'Верхняя'
    else:  # Следующая неделя
        start_date = current_date + timedelta(days=(7 - current_date.weekday()))
        week_type = 'Нижняя'

    full_schedule = []
    for i in range(6):
        # Определяем день
        single_day = start_date + timedelta(days=i)
        day = single_day.strftime("%A").lower()
        day_ru = {
            "monday": "понедельник",
            "tuesday": "вторник",
            "wednesday": "среда",
            "thursday": "четверг",
            "friday": "пятница",
            "saturday": "суббота",
        }.get(day)

        # Получаем расписание для дня
        schedule = get_full_schedule_for_day(day_ru, week_type)
        full_schedule.append(f"Расписание на {day_ru.capitalize()}:\n")

        if schedule:
            for row in schedule:
                time, room, subject, teacher = row
                full_schedule.append(
                    f"⏰ {time}\n📚 {subject}\n👨‍🏫 Преподаватель: {teacher or 'Не указан'}\n🚪 Аудитория: {room}\n\n"
                )
        else:
            full_schedule.append("Отсутствует.\n\n")

    return "\n".join(full_schedule)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Это бот для просмотра расписания группы 607-12.\n"
        "Выберите день недели, чтобы узнать расписание.\n"
        "Также вы можете использовать команду /help для получения помощи.",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text.lower() in [day.lower() for day in DAYS])
def send_schedule(message):
    day = message.text.lower()
    full_schedule = get_full_schedule_for_day(day, 'Верхняя')

    if not full_schedule:
        bot.send_message(message.chat.id, f"🚫 Расписание на {day.capitalize()} отсутствует.")
    else:
        result = f"📅 **Расписание на {day.capitalize()}**:\n\n"  # Заголовок с выделением

        for row in full_schedule:
            time, room, subject, teacher = row
            result += (
                f"*********************************\n"  # Разделительная линия
                f"⏰ Время: {time}\n"
                f"📚 Предмет: {subject}\n"
                f"👨‍🏫 Преподаватель: {teacher or 'Не указан'}\n"
                f"🚪 Аудитория: {room}\n"
                f"*********************************\n\n"  # Разделительная линия
            )

        bot.send_message(message.chat.id, result)

@bot.message_handler(func=lambda message: message.text == "Расписание текущей недели")
def send_current_week_schedule(message):
    schedule = get_schedule_for_week(0)
    bot.send_message(message.chat.id, schedule)

@bot.message_handler(func=lambda message: message.text == "Расписание следующей недели")
def send_next_week_schedule(message):
    schedule = get_schedule_for_week(1)
    bot.send_message(message.chat.id, schedule)

@bot.message_handler(commands=['week'])
def check_week_type(message):
    current_date = datetime.now()
    current_weekday = current_date.weekday()  # Получаем номер дня недели (0 = понедельник, 6 = воскресенье)

    # Определяем тип недели (замените логику на вашу актуальную)
    week_type = 'Верхняя' if (current_weekday // 7) % 2 == 0 else 'Нижняя'

    bot.send_message(message.chat.id, f"🔍 Сегодня {current_date.strftime('%Y-%m-%d')} и это {week_type} неделя.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Запустить бота\n"
        "/help - Показать доступные команды\n"
        "Выберите день недели - Узнать расписание на конкретный день\n"
        "Расписание текущей недели - Получить расписание на текущую неделю\n"
        "Расписание следующей недели - Получить расписание на следующую неделю\n"
        "/week - Узнать, какая неделя сейчас (верхняя или нижняя)"
    )
    bot.send_message(message.chat.id, help_text)

# Запуск Telegram-бота
if __name__ == "__main__":
    print("Telegram-бот запущен!")
    bot.polling(none_stop=True)
