import telebot
import requests
from datetime import datetime, timedelta
import logging
from telebot import types

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = "7357520387:AAGUpONfQVyDripQ2p0X_baziN_Q149eLSw"
bot = telebot.TeleBot(TOKEN)

currency_cache = {}
cache_duration = timedelta(hours=1)

currencies = [
    ("🇦🇺 Австралійський долар (AUD)", "AUD"),
    ("🇧🇷 Бразильський реал (BRL)", "BRL"),
    ("🇨🇦 Канадський долар (CAD)", "CAD"),
    ("🇨🇿 Чеська крона (CZK)", "CZK"),
    ("🇪🇺 Євро (EUR)", "EUR"),
    ("🇬🇧 Фунт стерлінгів (GBP)", "GBP"),
    ("🇭🇰 Гонконгський долар (HKD)", "HKD"),
    ("🇮🇩 Індонезійська рупія (IDR)", "IDR"),
    ("🇮🇱 Ізраїльський новий шекель (ILS)", "ILS"),
    ("🇯🇵 Японська єна (JPY)", "JPY"),
    ("🇰🇷 Південнокорейська вона (KRW)", "KRW"),
    ("🇲🇽 Мексиканське песо (MXN)", "MXN"),
    ("🇳🇿 Долар Нової Зеландії (NZD)", "NZD"),
    ("🇳🇴 Норвезька крона (NOK)", "NOK"),
    ("🇵🇱 Польський злотий (PLN)", "PLN"),
    ("🇸🇪 Шведська крона (SEK)", "SEK"),
    ("🇿🇦 Південноафриканський ранд (ZAR)", "ZAR"),
    ("🇦🇫 Афгані (AFN)", "AFN"),
    ("🇩🇰 Датська крона (DKK)", "DKK"),
    ("🇦🇷 Аргентинське песо (ARS)", "ARS"),
    ("🇻🇪 Венесуельський болівар (VES)", "VES"),
    ("🇵🇭 Філіппінське песо (PHP)", "PHP"),
    ("🇷🇺 Російський рубль (RUB)", "RUB"),
    ("🇧🇾 Білоруський рубль (BYN)", "BYN"),
    ("🇰🇿 Казахський тенге (KZT)", "KZT"),
    ("🇦🇲 Вірменський драм (AMD)", "AMD"),
    ("🇲🇩 Молдовський лей (MDL)", "MDL"),
    ("🇬🇪 Грузинський ларі (GEL)", "GEL"),
    ("🇹🇯 Таджицький сомоні (TJS)", "TJS"),
    ("🇺🇿 Узбецький сум (UZS)", "UZS"),
    ("🇺🇦 Українська гривня (UAH)", "UAH"),
    ("🇨🇳 Китайський юань (CNY)", "CNY"),
    ("🇹🇼 Тайванський новий долар (TWD)", "TWD"),
    ("🇸🇬 Сінгапурський долар (SGD)", "SGD"),
    ("🇹🇭 Тайський бат (THB)", "THB"),
    ("🇧🇪 Бельгійський франк (BEF)", "BEF"),
    ("🇭🇺 Угорський форінт (HUF)", "HUF"),
    ("🇻🇳 В'єтнамський донг (VND)", "VND"),
    ("🇮🇸 Ісландська крона (ISK)", "ISK"),
]

def fetch_exchange_rate(currency_code):
    today = datetime.today().strftime('%Y%m%d')
    bank_api = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency_code}&date={today}&json"
    
    try:
        response = requests.get(url=bank_api)
        response.raise_for_status()
        data = response.json()
        if data and "rate" in data[0]:
            return data[0]["rate"]
    except requests.RequestException as e:
        logging.error(f"Помилка при отриманні курсу для {currency_code}: {e}")
    return None

def get_exchange_rate(currency_code):
    current_time = datetime.now()
    
    if (currency_code in currency_cache and 
        current_time < currency_cache[currency_code]['expiry']):
        logging.info(f"Кеш: Курс {currency_code} знайдено в кеші.")
        return currency_cache[currency_code]['rate']

    rate = fetch_exchange_rate(currency_code)
    if rate is not None:
        currency_cache[currency_code] = {
            'rate': rate,
            'expiry': current_time + cache_duration
        }
        logging.info(f"Отримано курс {currency_code}: {rate}")
    else:
        logging.warning(f"Не вдалося отримати курс для {currency_code}.")
    return rate

def create_inline_keyboard(page=0):
    keyboard = types.InlineKeyboardMarkup()
    start_index = page * 5
    end_index = start_index + 5
    currency_slice = currencies[start_index:end_index]
    
    for name, code in currency_slice:
        keyboard.add(types.InlineKeyboardButton(text=name, callback_data=code))
    
    if start_index > 0:
        keyboard.add(types.InlineKeyboardButton(text="Назад", callback_data=f"page:{page - 1}"))
    if end_index < len(currencies):
        keyboard.add(types.InlineKeyboardButton(text="Далі", callback_data=f"page:{page + 1}"))
    
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = create_inline_keyboard()
    welcome_message = (
        "*Привіт!*\n"
        "Цей бот дозволяє отримувати курси валют.\n"
        "Бот був розроблений саншайном.\n"
        "Виберіть валюту для отримання курсу:"
    )
    bot.send_message(message.chat.id, welcome_message, reply_markup=keyboard, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_currency_selection(call):
    if call.data.startswith("page:"):
        page_number = int(call.data.split(":")[1])
        keyboard = create_inline_keyboard(page_number)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    else:
        currency_code = call.data.strip().upper()
        logging.info(f"Користувач вибрав валюту: {currency_code}")
        rate = get_exchange_rate(currency_code)
        
        if rate is not None:
            bot.answer_callback_query(call.id)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            rate_message = f"Курс {currency_code} на сьогодні: {rate:.2f} грн."
            keyboard = types.InlineKeyboardMarkup()
            bot.send_message(call.message.chat.id, rate_message, reply_markup=keyboard)
        else:
            bot.answer_callback_query(call.id, "Помилка: Таку валюту не знайдено.", show_alert=True)

if __name__ == "__main__":
    logging.info("Бот запущений.")
    bot.infinity_polling(none_stop=True, interval=0)