
import telebot
import yt_dlp
import os
import json
from telebot import types

TOKEN = "8609217953:AAHzPNw0xSpuUqINYqQf-UOMP981TPOm9wc"
ADMIN_ID = 5633684726
CHANNEL = "@telefon_reklama_xizmati"

bot = telebot.TeleBot(TOKEN)

# ================== USERS ==================

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def total_users():
    return len(load_users())

# ================== OBUNA TEKSHIRISH ==================

def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

# ================== START ==================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    # Admin bo'lsa panelini ko'rsatish
    if user_id == ADMIN_ID:
        show_admin_panel(message)

    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL[1:]}")
        markup.add(btn)
        bot.send_message(message.chat.id,
                         "❗ Botdan foydalanish uchun kanalga obuna bo‘ling!",
                         reply_markup=markup)
        return

    add_user(user_id)

    # Admin uchun userlar sonini ko‘rsatish
    user_count_text = f"\n\n👥 Userlar: {total_users()} ta" if user_id == ADMIN_ID else ""

    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📥 Yuklash", callback_data="download_video")
    markup.add(btn)

    bot.send_message(message.chat.id,
                     f"👋 Salom!\n\n"
                     f"📥 Instagram va TikTok video yuklab beraman"
                     f"{user_count_text}\n\n"
                     f"🔗 Link yubor va 📥 tugmasini bosing!",
                     reply_markup=markup)

# ================== ADMIN PANEL ==================

def show_admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📊 Statistika", "📢 Xabar yuborish")
    bot.send_message(message.chat.id, "⚙️ Admin panel", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
        return
    show_admin_panel(message)

# ================== ADMIN BUTTONS ==================

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, f"👥 Jami userlar: {total_users()} ta")

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")
def ask_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "✍️ Xabarni yoz:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    users = load_users()
    success = 0
    for user in users:
        try:
            bot.send_message(user, message.text)
            success += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ Yuborildi: {success} ta")

# ================== VIDEO YUKLASH ==================

def download(url):
    ydl_opts = {
        'outtmpl': 'media.%(ext)s',
        'format': 'best'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

user_links = {}  # foydalanuvchi yuborgan linkni saqlash

@bot.message_handler(func=lambda m: "instagram.com" in m.text or "tiktok.com" in m.text)

def get_link(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        bot.send_message(message.chat.id, "❗ Avval kanalga obuna bo‘ling!")
        return
    user_links[user_id] = message.text
    bot.send_message(message.chat.id, "🔹 Link saqlandi! Endi 📥 tugmasini bosing.")

@bot.callback_query_handler(func=lambda c: c.data == "download_video")
def callback_download(call):
    user_id = call.from_user.id
    if user_id not in user_links:
        bot.answer_callback_query(call.id, "❗ Avval link yuboring!")
        return

    url = user_links[user_id]
    msg = bot.send_message(call.message.chat.id, "⏳ Yuklanmoqda...")

    try:
        download(url)
        sent = False
        for file in os.listdir():
            if file.startswith("media"):
                with open(file, 'rb') as f:
                    if file.endswith((".jpg", ".png", ".jpeg")):
                        bot.send_photo(call.message.chat.id, f)
                    else:
                        bot.send_video(call.message.chat.id, f)
                os.remove(file)
                sent = True
        if not sent:
            bot.send_message(call.message.chat.id, "❌ Bu videoni yuklab bo‘lmadi!")

        bot.delete_message(call.message.chat.id, msg.message_id)
        bot.answer_callback_query(call.id, "✅ Yuklandi!")
        del user_links[user_id]

    except Exception as e:
        bot.send_message(call.message.chat.id,
                         "❌ Bu videoni yuklab bo‘lmadi!\n🔒 Video private yoki link noto‘g‘ri.")
        print(e)
        bot.answer_callback_query(call.id, "❌ Xatolik yuz berdi!")

# ================== START BOT ==================

bot.polling()