import decimal
from textwrap import dedent

import aiogram.utils.markdown as md

from cost_my_chemo_bot.db import Category, Course, Nosology

WELCOME = "Здравствуйте! Это чат-бот онкологической «Клиники доктора Ласкова» (hemonc.ru). Я предназначен для оценки стоимости химиотерапии в нашей клинике. Для расчёта понадобятся рост и вес человека, который будет лечиться, и схема лечения/назначенный препарат. Важно: в результате расчета вы получите стоимость одного курса (введения).  Начнём?"
START = "Спасибо. Для расчёта понадобятся рост и вес человека, который будет лечиться, и схема лечения/назначенный препарат. Важно: в результате расчета вы получите стоимость одного курса (введения).  Начнём?"

HEIGHT_INPUT = (
    "Пожалуйста, введите рост человека, для которого предназначен курс, в сантиметрах."
)
HEIGHT_WRONG = "Это не число. Введите рост в сантиметрах."
WEIGHT_INPUT = "А теперь её/его вес в килограммах."
WEIGHT_WRONG = "Это не число. Введите вес килограммах."
CATEGORY_CHOOSE = "Чтобы рассчитать стоимость лечения, выберите область, к которой относится заболевание. В разделе «Сопроводительная терапия» можно узнать цену некоторых дополнительных препаратов."
CATEGORY_WRONG = "Неверно выбрана область. Выберите область на клавиатуре."
NOSOLOGY_CHOOSE = "Теперь выберите заболевание:"
NOSOLOGY_WRONG = "Неверно выбрано заболевание. Выберите заболевание на клавиатуре."
COURSE_CHOOSE = (
    "Выберите название курса или препарата. Эта информация обычно есть в выписке."
)
COURSE_WRONG = (
    "Неверно выбран курс или препарат. Выберите курс или препарат на клавиатуре."
)
CUSTOM_COURSE_INPUT = "Напишите название курса, который вы искали, или названия препаратов – и мы рассчитаем их стоимость."
DATA_CONFIRMATION = dedent(
    """
    Спасибо! Вы указали все нужные данные. Проверьте, пожалуйста, всё ли так? 
    Рост: {height} см
    Вес: {weight} кг
    Раздел: {category_name}
    Заболевание: {nosology_name}
    Курс: {course_name}
    Всё верно?
"""
)
PRICE_FOR_CUSTOM_COURSE = "Цена по запросу"
CURRENCY = "рублей"
DATA_CORRECT = dedent(
    """
    Отлично! Стоимость курса составит: {course_price}
    Расчет был выполнен для пациента с такими данными и заболеванием:
    Рост: {height} см
    Вес: {weight} кг
    Раздел: {category_name}
    Заболевание: {nosology_name}
    Курс: {course_name}

    Вы можете сохранить это сообщение, отправив его себе (нажмите на сообщение, выберите «Переслать» -> «Сохранённые»).
    Если вы хотите обсудить лечение у нас, отправьте нам номер телефона и email (любой пункт можно пропустить). Мы свяжемся с вами в течение рабочего дня.
    А если вы хотите обратиться в «Клинику доктора Ласкова» самостоятельно, напишите @klinikalaskova_bot, на почту info@hemonc.ru или позвоните +7 499 112-25-06. Будем рады помочь вам!
"""
)
LEAD_FIRST_NAME = "Введите ваше имя"
LEAD_LAST_NAME = "Введите вашу фамилию"
LEAD_EMAIL = "Введите ваш email"
LEAD_EMAIL_WRONG = "Неверно введен email. Введите email."
LEAD_PHONE_NUMBER = (
    "Введите ваш номер телефона в международном формате.\n"
    "Например: +7 999 999 99 99 для России или +375 99 999 99 99 для Беларуси."
)
LEAD_PHONE_NUMBER_WRONG = f"Неверно введен номер телефона. {LEAD_PHONE_NUMBER}"
LEAD_CONFIRMATION = dedent(
    """
    Спасибо! Давайте проверим. Вы указали:

    Имя: {first_name}
    Фамилия: {last_name}
    E-mail: {email}
    Номер телефона: {phone_number}

    Всё правильно?
"""
)
FINAL_MESSAGE = "Отлично. Мы свяжемся с вами в течение рабочего дня."
GOODBYE = "До свидания!"


def course_selected(
    height: int,
    weight: int,
    category: Category,
    nosology: Nosology,
    course: Course,
    course_price: decimal.Decimal,
) -> str:
    return md.text(
        md.text("Рост:", md.bold(height)),
        md.text("Вес:", md.code(weight)),
        md.text("Категория:", md.italic(category.categoryName)),
        md.text("Подкатегория:", md.italic(nosology.nosologyName)),
        md.text("Курс:", course.Course),
        md.text("Цена:", f"{course_price:.2f}".replace(".", ",")),
        sep="\n",
    )
