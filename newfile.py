import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from geopy.geocoders import Nominatim

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

cities = {}
page_size = 12
current_page = 0

def load_cities():
    try:
        with open('jopa.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ' - ' not in line:
                    continue
                city, addresses = line.strip().split(' - ', 1)
                cities[city.strip()] = [addr.strip() for addr in addresses.split(';') if addr.strip()]
    except FileNotFoundError:
        logger.error("File 'jopa.txt' not found!")

load_cities()

def create_buttons(page):
    keyboard = []
    city_names = list(cities.keys())
    start_index = page * page_size
    end_index = start_index + page_size
    
    for city in city_names[start_index:end_index]:
        keyboard.append([InlineKeyboardButton(city, callback_data=f"CITY_{city}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀ Назад", callback_data="PREV_PAGE"))
    if end_index < len(city_names):
        nav_buttons.append(InlineKeyboardButton("Вперед ▶", callback_data="NEXT_PAGE"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext) -> None:
    global current_page
    current_page = 0
    await update.message.reply_text(
        "Привет! Выбери город:",
        reply_markup=create_buttons(current_page),
        parse_mode='HTML'
    )

async def handle_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    global current_page
    
    if query.data == "PREV_PAGE":
        current_page = max(0, current_page - 1)
        await query.edit_message_text(
            text="Выбери город:",
            reply_markup=create_buttons(current_page),
            parse_mode='HTML'
        )
        
    elif query.data == "NEXT_PAGE":
        current_page += 1
        await query.edit_message_text(
            text="Выбери город:",
            reply_markup=create_buttons(current_page),
            parse_mode='HTML'
        )
        
    elif query.data.startswith("CITY_"):
        city_name = query.data[5:]
        addresses = cities.get(city_name, [])
        
        geolocator = Nominatim(user_agent="unique_geo_bot_app")
        results = []
        
        for address in addresses[:3]:
            try:
                location = geolocator.geocode(address)
                if location:
                    # Форматирование координат с 7 знаками после точки
                    lat = f"{location.latitude:.7f}"
                    lon = f"{location.longitude:.7f}"
                    results.append(
                        f"📍 <b>{address}</b>\n"
                        f"🌐 Широта: <code>{lat}</code>\n"
                        f"🌐 Долгота: <code>{lon}</code>\n"
                      
                    )
            except Exception as e:
                logger.error(f"Geocoding error: {e}")
        
        response = "\n".join(results) if results else "❌ Координаты не найдены"
        await query.edit_message_text(
            text=response,
            reply_markup=create_buttons(current_page),
            parse_mode='HTML'
        )

async def post_init(application):
    logger.info("Бот успешно инициализирован")

def main() -> None:
    TOKEN = "7375866062:AAHgneTNZ9wZWImdTu6Alya1uMhpXGJCHvU"
    
    application = ApplicationBuilder() \
        .token(TOKEN) \
        .post_init(post_init) \
        .build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_button))
    
    application.run_polling(
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == '__main__':
    main()
