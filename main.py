import os
import json
import uuid
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify
import telebot

# ==================== CẤU HÌNH & KHỞI TẠO ====================

# Nhập Token Bot Telegram của bạn vào đây (hoặc đặt trong biến môi trường Render)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "THAY_BOT_TOKEN_TELEGRAM_CUAP_BAN_VAO_DAY")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

TOKENS_FILE = "tokens.txt"
GARENA_GUEST_URL = "https://100067.connect.garenanow.com/guest/login"

# ==================== 1. TỰ ĐỘNG SINH TOKEN GUEST ====================

def create_single_guest_token(_):
    device_id = str(uuid.uuid4()).replace("-", "")[:16]
    payload = {
        "device_id": device_id,
        "app_id": 100067,
        "sdk_version": "2.0.0"
    }
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)",
        "Content-Type": "application/json; charset=UTF-8"
    }
    try:
        res = requests.post(GARENA_GUEST_URL, data=json.dumps(payload), headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("access_token") or data.get("token")
    except Exception:
        pass
    return None

def generate_tokens_pool(count=100):
    tokens = set()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(create_single_guest_token, range(count))
        for t in results:
            if t:
                tokens.add(t)
    
    token_list = list(tokens)
    if token_list:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            for t in token_list:
                f.write(f"{t}\n")
    return token_list

# ==================== 2. CHECK TOKEN & SOI PROFILE ====================

def check_token_live(token):
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalProfile"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)"
    }
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            return token
    except Exception:
        pass
    return None

def get_player_profile(target_uid, token, region="VN"):
    url = f"https://clientbp.ggblueshark.com/GetPlayerPersonalProfile?uid={target_uid}&region={region}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            acc = data.get("AccountInfo", {})
            clan = data.get("ClanInfo", {})
            return {
                "nickname": acc.get("Nickname", "N/A"),
                "level": acc.get("Level", 0),
                "likes": acc.get("Likes", 0),
                "exp": acc.get("Exp", 0),
                "clan_name": clan.get("ClanName", "Chưa vào quân đoàn"),
                "clan_level": clan.get("ClanLevel", 0)
            }
    except Exception:
        pass
    return None

# ==================== 3. HÀM BẮN LIKE ĐA LUỒNG ====================

def send_like_request(token, target_uid, region="VN"):
    url = f"https://clientbp.ggblueshark.com/LikeProfile?uid={target_uid}&region={region}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return True
    except Exception:
        pass
    return False

# ==================== 4. XỬ LÝ LỆNH BOT TELEGRAM ====================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = (
        "🤖 **BOT BUFF LIKE & SOI ACC FREE FIRE**\n\n"
        "📌 **Các lệnh khả dụng:**\n"
        "🔹 `/check <UID>` : Soi Tên, Level, Like, Quân đoàn.\n"
        "🔹 `/buff <UID>` : Buff Like Đa Luồng siêu tốc.\n"
        "🔹 `/renew` : Làm mới 100 Token Guest Garena."
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['renew'])
def handle_renew(message):
    bot.reply_to(message, "🔄 Đang khởi tạo 100 Token Guest mới...")
    tokens = generate_tokens_pool(100)
    bot.reply_to(message, f"✅ Đã tạo thành công `{len(tokens)}` Token mới!", parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def handle_check(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Vui lòng nhập cú pháp: `/check <UID>`", parse_mode="Markdown")
        return

    uid = args[1]
    bot.reply_to(message, f"🔍 Đang kiểm tra thông tin UID `{uid}`...", parse_mode="Markdown")

    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            tokens = [line.strip() for line in f if line.strip()]
    except Exception:
        tokens = []

    if not tokens:
        tokens = generate_tokens_pool(10)

    profile = get_player_profile(uid, tokens[0])
    if profile:
        text = (
            f"👤 **THÔNG TIN TÀI KHOẢN FREE FIRE**\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"🎮 **Tên In-game**: `{profile['nickname']}`\n"
            f"🆔 **UID**: `{uid}`\n"
            f"⭐ **Cấp Độ (Level)**: `{profile['level']}`\n"
            f"❤️ **Lượt Like**: `{profile['likes']}`\n"
            f"🛡️ **Quân Đoàn**: `{profile['clan_name']}` (Lv {profile['clan_level']})\n"
            f"➖➖➖➖➖➖➖➖➖➖"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Không thể lấy thông tin UID này!")

@bot.message_handler(commands=['buff'])
def handle_buff(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Vui lòng nhập cú pháp: `/buff <UID>`", parse_mode="Markdown")
        return

    uid = args[1]
    bot.reply_to(message, f"🔥 Đang lọc Token và chuẩn bị xả Like vào UID `{uid}`...", parse_mode="Markdown")

    # Đọc token
    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            raw_tokens = [line.strip() for line in f if line.strip()]
    except Exception:
        raw_tokens = []

    if not raw_tokens:
        raw_tokens = generate_tokens_pool(100)

    # Lọc Token Live
    with ThreadPoolExecutor(max_workers=20) as executor:
        live_tokens = [t for t in executor.map(check_token_live, raw_tokens) if t]

    if not live_tokens:
        bot.reply_to(message, "❌ Không có Token nào sống để buff. Vui lòng gõ `/renew` trước!")
        return

    # Check trước khi buff
    before = get_player_profile(uid, live_tokens[0])
    likes_before = before['likes'] if before else "N/A"

    # Bắn like
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(lambda t: send_like_request(t, uid), live_tokens)
        success_count = sum(1 for r in results if r)

    # Check sau khi buff
    after = get_player_profile(uid, live_tokens[0])
    likes_after = after['likes'] if after else "N/A"

    text = (
        f"🎉 **BUFF LIKE HOÀN TẤT!**\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎮 **Tên**: `{before['nickname'] if before else 'N/A'}`\n"
        f"🆔 **UID**: `{uid}`\n"
        f"❤️ **Like trước**: `{likes_before}`\n"
        f"🚀 **Like đã tăng**: `+{success_count}`\n"
        f"📊 **Like hiện tại**: `{likes_after}`\n"
        f"➖➖➖➖➖➖➖➖➖➖"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# ==================== 5. FLASK HEALTH CHECK CHO RENDER ====================

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "Bot Free Fire Server đang chạy!"}), 200

def run_bot():
    bot.infinity_polling(skip_pending=True)

# ==================== 6. CHẠY SONG SONG BOT & WEB ====================

if __name__ == "__main__":
    # Chạy Telegram Bot ở luồng phụ (Thread)
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Chạy Flask Web Server ở luồng chính giữ cổng PORT cho Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
