import asyncio  # Импортируем библиотеку asyncio для работы с асинхронным программированием
import logging  # Импортируем библиотеку logging для логирования
from datetime import datetime  # Импортируем класс datetime для работы с датой и временем

# Импортируем необходимые классы из библиотеки aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Импортируем хранилище для состояний
from aiogram.dispatcher import FSMContext  # Импортируем контекст для работы с состояниями
from aiogram.dispatcher.filters import CommandStart  # Импортируем фильтр для команды /start
from aiogram.dispatcher.filters.state import State, StatesGroup  # Импортируем классы для работы с состояниями
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove  # Импортируем необходимые типы для работы с сообщениями и клавиатурами
import os  # Импортируем модуль os для работы с операционной системой
from dotenv import load_dotenv  # Импортируем функцию для загрузки переменных окружения из .env файла

load_dotenv()  # Загружаем переменные окружения из файла .env
bot = Bot(token=os.getenv('TOKEN'))  # Создаём экземпляр бота, передавая токен из переменных окружения
dp = Dispatcher(bot, storage=MemoryStorage())  # Создаём диспетчер для обработки сообщений, используя хранилище состояний в памяти


async def run_bot():
    await dp.start_polling()  # Начинаем опрос обновлений от Telegram


# Создание клавиатуры для стартового меню
kb_init = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Рассчитать'), KeyboardButton(text='Информация')]  # Кнопки "Рассчитать" и "Информация"
], resize_keyboard=True)  # Настраиваем клавиатуру на автоматическое изменение размера

# Создание Inline клавиатуры
inline_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')],  # Кнопка для расчета калорий
    [InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas')]  # Кнопка для получения формул
])


# Определение состояний для машины состояний
class UserState(StatesGroup):
    age = State()  # Состояние для ввода возраста
    height = State()  # Состояние для ввода роста
    weight = State()  # Состояние для ввода веса
    gender = State()  # Состояние для выбора пола


@dp.message_handler(CommandStart())  # Обработчик для команды /start
async def start_message(message: Message):
    await message.answer('Привет! Я бот, помогающий твоему здоровью.', reply_markup=kb_init)  # Ответ пользователю с приветствием и клавиатурой


@dp.message_handler(lambda message: message.text == 'Информация')  # Обработчик для текста "Информация"
async def information(message: Message):
    await message.answer("С помощью этого бота вы можете рассчитать свою норму калорий\n"
                         "Для расчёта используется формула Миффлина — Сан Жеора\n"
                         "Чтобы приступить, нажмите кнопку 'Рассчитать'")  # Ответ с информацией о ботe


@dp.message_handler(lambda message: message.text == 'Рассчитать')  # Обработчик для текста "Рассчитать"
async def main_menu(message: Message):
    await message.answer("Выберите опцию:", reply_markup=inline_kb)  # Ответ с предложением выбрать опцию и Inline клавиатурой


# Обработка нажатия на кнопку Формулы расчёта
@dp.callback_query_handler(lambda call: call.data == 'formulas')  # Обработчик для нажатия на кнопку "Формулы расчёта"
async def get_formulas(call: types.CallbackQuery):
    await call.message.answer(  # Ответ с формулой расчёта
        "Формула Миффлина — Сан Жеора:\n"
        "Для мужчин: (10 × вес) + (6.25 × рост) - (5 × возраст) + 5\n"
        "Для женщин: (10 × вес) + (6.25 × рост) - (5 × возраст) - 161"
    )
    await call.answer()  # Подтверждаем обработку нажатия кнопки


# Обработка нажатия на кнопку Рассчитать норму калорий
@dp.callback_query_handler(lambda call: call.data == 'calories')  # Обработчик для нажатия на кнопку "Рассчитать норму калорий"
async def get_gender(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Выберите свой пол:", reply_markup=InlineKeyboardMarkup(  # Запрос пола у пользователя
        inline_keyboard=[
            [InlineKeyboardButton(text='Мужчина', callback_data='male'),  # Кнопка для выбора "Мужчина"
             InlineKeyboardButton(text='Женщина', callback_data='female')]  # Кнопка для выбора "Женщина"
        ]
    ))
    await state.set_state(UserState.gender)  # Устанавливаем состояние для выбора пола
    await call.answer()  # Подтверждаем обработку нажатия кнопки


# Этап выбора пола и дальнейший каскад действий
@dp.callback_query_handler(lambda call: call.data in ['male', 'female'], state=UserState.gender)  # Обработчик для выбора пола
async def set_gender(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(gender=call.data)  # Сохраняем выбранный пол в состоянии

    # Убираем инлайновую клавиатуру выбора пола, путем редактирования сообщения
    await call.message.edit_reply_markup(reply_markup=None)  # Удаляем клавиатуру из сообщения

    await call.message.answer("Введите свой рост в сантиметрах:", reply_markup=ReplyKeyboardRemove())  # Запрос роста у пользователя
    await state.set_state(UserState.height)  # Устанавливаем состояние для ввода роста
    await call.answer()  # Подтверждаем обработку нажатия кнопки


@dp.message_handler(state=UserState.height)  # Обработчик для ввода роста
async def set_weight(message: Message, state: FSMContext):
    await state.update_data(height=message.text)  # Сохраняем введённый рост в состоянии
    await message.answer("Введите свой вес в килограммах:")  # Запрос веса у пользователя
    await state.set_state(UserState.weight)  # Устанавливаем состояние для ввода веса


@dp.message_handler(state=UserState.weight)  # Обработчик для ввода веса
async def set_age(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)  # Сохраняем введённый вес в состоянии
    await message.answer("Укажите ваш возраст:")  # Запрос возраста у пользователя
    await state.set_state(UserState.age)  # Устанавливаем состояние для ввода возраста


@dp.message_handler(state=UserState.age)  # Обработчик для ввода возраста
async def send_calories(message: Message, state: FSMContext):
    try:
        await state.update_data(age=message.text)  # Сохраняем введённый возраст в состоянии
        data = await state.get_data()  # Получаем данные из состояния

        calories = 0  # Переменная для хранения рассчитанных калорий
        age = int(data['age'])  # Преобразуем возраст в целое число
        height = float(data['height'])  # Преобразуем рост в число с плавающей запятой
        weight = float(data['weight'])  # Преобразуем вес в число с плавающей запятой
        gender = data['gender']  # Получаем пол из состояния

        # Рассчитываем норму калорий в зависимости от пола
        if gender == 'male':
            calories = (10 * weight) + (6.25 * height) - (5 * age) + 5
        elif gender == 'female':
            calories = (10 * weight) + (6.25 * height) - (5 * age) - 161
        else:
            await message.answer("Убедитесь, что вы выбрали пол корректно.")  # Проверяем корректность выбора пола
            return

        await message.answer(f"Ваша норма калорий: {calories:.2f}", reply_markup=kb_init)  # Отправляем результат пользователю

    except ValueError:  # Обработка ошибок при преобразовании данных
        await message.answer("Пожалуйста, вводите только числа. Попробуйте ещё раз.", reply_markup=kb_init)  # Сообщение об ошибке
    finally:
        await state.finish()  # Завершаем состояние


@dp.message_handler()  # Обработчик для всех остальных сообщений
async def all_messages(message: Message):
    await message.answer("Введите команду /start, чтобы начать общение.")  # Сообщение с инструкцией


if __name__ == "__main__":  # Проверяем, что скрипт запускается напрямую, а не импортируется как модуль
    logging.basicConfig(level=logging.INFO)  # Настраиваем уровень логирования на INFO для вывода сообщений
    print(datetime.now())  # Выводим текущее время и дату в консоль
    try:
        asyncio.run(run_bot())  # Запускаем асинхронную функцию run_bot() для начала работы бота
    except KeyboardInterrupt:  # Обрабатываем исключение, возникающее при прерывании программы (например, Ctrl+C)
        print('Exit')  # Выводим сообщение о завершении работы бота