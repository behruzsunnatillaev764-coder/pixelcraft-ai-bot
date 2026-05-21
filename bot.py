import telebot
import requests
import time
from io import BytesIO
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton

# ==========================
# TOKENLAR
# ==========================
BOT_TOKEN = "8481399913:AAGva28QmyjZ7RfE0wkaiXjPfLNWYNQYxkc"
HF_TOKEN = "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"

# ==========================
# ADMIN & PREMIUM
# ==========================
ADMIN_ID = 5702511489

CARD = """
4916 9903 0207 5020
4413 5976 0452 9683
"""

premium_users = []
waiting_check = []

# ==========================
# LIMIT
# ==========================
MAX_IMAGES = 3
RESET_TIME = 86400

# ==========================
# BOT
# ==========================
bot = telebot.TeleBot(BOT_TOKEN)

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

# ==========================
# USER DATA
# ==========================
users = {}

# ==========================
# START
# ==========================
@bot.message_handler(commands=['start'])
def start(message):

    markup = InlineKeyboardMarkup()

    create_btn = InlineKeyboardButton(
        "🎨 Rasm yaratish",
        callback_data="create_image"
    )

    premium_btn = InlineKeyboardButton(
        "💎 Premium olish",
        callback_data="premium_menu"
    )

    markup.add(create_btn)
    markup.add(premium_btn)

    text = """
🎨 AI Image Generator Bot

🖼 Prompt yuboring va AI rasm yaratadi.

💎 Premium:
• Limitsiz rasm
• HD sifat
• Tez generatsiya
"""

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )

# ==========================
# CALLBACK
# ==========================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    data = call.data

    # premium menu
    if data == "premium_menu":

        waiting_check.append(call.from_user.id)

        text = f"""
💎 Premium sotib olish

💳 Kartalar:
{CARD}

💰 Narx: 10 000 so'm

📸 To'lovdan keyin chek screenshot yuboring.
"""

        bot.send_message(
            call.message.chat.id,
            text
        )

    # create image
    elif data == "create_image":

        bot.send_message(
            call.message.chat.id,
            "🎨 Prompt yuboring."
        )

# ==========================
# CHEK
# ==========================
@bot.message_handler(content_types=['photo'])
def check_photo(message):

    user_id = message.from_user.id

    if user_id not in waiting_check:
        return

    photo = message.photo[-1].file_id

    bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""
💳 Yangi premium so'rov

👤 {message.from_user.first_name}

🆔 ID: {user_id}

✅ Premium berish:

/addpremium {user_id}

❌ Bekor qilish:

/deny {user_id}
"""
    )

    bot.reply_to(
        message,
        "✅ Chek adminga yuborildi.\n⏳ Tekshirilmoqda."
    )

# ==========================
# PREMIUM BERISH
# ==========================
@bot.message_handler(commands=['addpremium'])
def add_premium(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        user_id = int(message.text.split()[1])

        if user_id not in premium_users:
            premium_users.append(user_id)

        bot.send_message(
            user_id,
            "🎉 Premium aktiv qilindi!\n♾ Endi sizda limitsiz rasm yaratish mavjud."
        )

        bot.reply_to(
            message,
            "✅ Premium berildi."
        )

    except:

        bot.reply_to(
            message,
            "❌ Xato"
        )

# ==========================
# PREMIUM BEKOR
# ==========================
@bot.message_handler(commands=['deny'])
def deny(message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        user_id = int(message.text.split()[1])

        bot.send_message(
            user_id,
            "❌ To'lov tasdiqlanmadi."
        )

        bot.reply_to(
            message,
            "❌ Bekor qilindi."
        )

    except:

        bot.reply_to(
            message,
            "❌ Xato"
        )

# ==========================
# IMAGE GENERATE
# ==========================
@bot.message_handler(func=lambda m: True)
def generate_image(message):

    user_id = message.from_user.id
    current_time = time.time()

    # premium bo'lmasa limit ishlaydi
    if user_id not in premium_users:

        # yangi user
        if user_id not in users:

            users[user_id] = {
                "count": 0,
                "time": current_time
            }

        # 24 soat reset
        if current_time - users[user_id]["time"] >= RESET_TIME:

            users[user_id]["count"] = 0
            users[user_id]["time"] = current_time

        # limit
        if users[user_id]["count"] >= MAX_IMAGES:

            remaining = int(
                RESET_TIME - (
                    current_time - users[user_id]["time"]
                )
            )

            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            bot.reply_to(
                message,
                f"""
❌ Siz kunlik limitni tugatdingiz.

⏳ 24 soatdan keyin qayta urinib ko'ring.
🕒 {hours} soat {minutes} minut qoldi.

💎 Premium olish:
/start
"""
            )

            return

        # limit +1
        users[user_id]["count"] += 1

    # loading
    msg = bot.reply_to(
        message,
        "⏳ Rasm yaratilmoqda..."
    )

    try:

        prompt = f"""
{message.text},
ultra realistic,
cinematic lighting,
4k,
detailed,
professional photography
"""

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json={"inputs": prompt},
            timeout=300
        )

        if response.status_code != 200:
            raise Exception(response.text)

        image = BytesIO(response.content)
        image.name = "image.png"

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

        # premium
        if user_id in premium_users:

            caption = """
✅ Tayyor!
💎 Premium user
♾ Limitsiz foydalanish
"""

        else:

            left = MAX_IMAGES - users[user_id]["count"]

            caption = f"""
✅ Tayyor!
📊 Qolgan limit: {left}/3
"""

        bot.send_photo(
            message.chat.id,
            image,
            caption=caption
        )

    except Exception as e:

        bot.edit_message_text(
            f"❌ Xatolik:\n{e}",
            message.chat.id,
            msg.message_id
        )

# ==========================
# RUN
# ==========================
print("Bot ishga tushdi...")
bot.infinity_polling()




