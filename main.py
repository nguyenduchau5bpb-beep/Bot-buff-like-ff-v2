import os
import json
import uuid
import random
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify
import telebot

# ==================== CẤU HÌNH & KHỞI TẠO ====================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "THAY_BOT_TOKEN_TELEGRAM_CUA_BAN_VAO_DAY")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

TOKENS_FILE = "tokens.txt"

GARENA_ENDPOINTS = [
    "https://100067.connect.garenanow.com/guest/login",
    "https://connect.garenanow.com/guest/login",
    "https://100067.connect.garena.com/guest/login"
]

USER_AGENTS = [
    "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)",
    "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B Build/SP1A.210812.016)",
    "Dalvik/2.1.0 (Linux; U; Android 10; M2007J20CG Build/QKQ1.200512.002)",
    "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TP1A.220624.021)"
]

# ==================== 1. TỰ ĐỘNG SINH TOKEN GUEST ====================

def create_single_guest_token(_):
    device_id = str(uuid.uuid4()).replace("-", "")[:16]
    payload = {
        "device_id": device_id,
        "app_id": 100067,
        "sdk_version": "2.0.0",
        "device_model": "Xiaomi M2010J19SG",
        "os_version": "11"
    }
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/json; charset=UTF-8",
        "Connection": "Keep-Alive"
    }
    
    last_err = ""
    for endpoint in GARENA_ENDPOINTS:
        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                token = data.get("access_token") or data.get("token") or data.get("session_key")
                if token:
                    return (True, token)
                else:
                    last_err = f"Response không có token: {res.text[:100]}"
            else:
                last_err = f"HTTP {res.status_code}: {res.text[:100]}"
        except Exception as e:
            last_err = f"Lỗi kết nối ({type(e).__name__}): {str(e)}"
            
    return (False, last_err)

def generate_tokens_pool(count=50):
    tokens = set()
    errors = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(create_single_guest_token, range(count))
        for success, res in results:
            if success:
                tokens.add(res)
            else:
                if res not in errors and len(errors) < 3:
                    errors.append(res)
    
    token_list = list(tokens)
    if token_list:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            for t in token_list:
                f.write(f"{t}\n")
                
    return token_list, errors

# ==================== 2. CHECK TOKEN & SOI PROFILE ====================

def check_token_live(token):
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalProfile"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": random.choice(USER_AGENTS)
    }
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            return token
    except Exception:
        pass
    return None

def get_player_profile_detailed(target_uid, token, region="VN"):
    """Lấy thông tin và trả về kèm chi tiết lỗi nếu thất bại"""
    url = f"https://clientbp.ggblueshark.com/GetPlayerPersonalProfile?uid={target_uid}&region={region}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": random.choice(USER_AGENTS)
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            acc = data.get("AccountInfo", {})
            clan = data.get("ClanInfo", {})
            if not acc.get("Nickname"):
                return False, f"Server trả về dữ liệu rỗng (UID `{target_uid}` có thể sai hoặc không tồn tại)."
            
            return True, {
                "nickname": acc.get("Nickname", "N/A"),
                "level": acc.get("Level", 0),
                "likes": acc.get("Likes", 0),
                "exp": acc.get("Exp", 0),
                "clan_name": clan.get("ClanName", "Chưa vào quân đoàn"),
                "clan_level": clan.get("ClanLevel", 0)
            }
        else:
            return False, f"Mã lỗi HTTP {res.status_code} từ Garena API.\nChi tiết: `{res.text[:150]}`"
    except Exception as e:
        return False, f"Lỗi ngoại lệ khi gọi API Garena: `{type(e).__name__}: {str(e)}`"

# ==================== 3. HÀM BẮN LIKE ====================

def send_like_request(token, target_uid, region="VN"):
    url = f"https://clientbp.ggblueshark.com/LikeProfile?uid={target_uid}&region={region}"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": random.choice(USER_AGENTS)
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
        "📌 **Danh sách lệnh đầy đủ:**\n"
        "🔹 `/check <UID>` : Soi Tên, Level, Like, Quân đoàn.\n"
        "🔹 `/buff <UID>` | `/bufflike <UID>` | `/like <UID>` : Buff Like Đa Luồng.\n"
        "🔹 `/renew` : Tạo danh sách Token Guest mới."
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['renew'])
def handle_renew(message):
    bot.reply_to(message, "🔄 Đang gửi request tạo Token Guest mới...")
    tokens, errors = generate_tokens_pool(50)
    if tokens:
        bot.reply_to(message, f"✅ Đã tạo thành công `{len(tokens)}` Token mới!", parse_mode="Markdown")
    else:
        err_msg = "\n".join([f"• `{e}`" for e in errors]) if errors else "Không xác định"
        msg = (
            "❌ **Tạo Token Thất Bại (0 Token)**\n\n"
            "🔍 **Lý do chi tiết từ Server/Render:**\n"
            f"{err_msg}"
        )
        bot.reply_to(message, msg, parse_mode="Markdown")

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
        tokens, _ = generate_tokens_pool(20)

    if not tokens:
        bot.reply_to(message, "❌ **LỖI:** Danh sách Token đang trống! Vui lòng gõ `/renew` để kiểm tra lý do tạo token lỗi.", parse_mode="Markdown")
        return

    success, result = get_player_profile_detailed(uid, tokens[0])
    if success:
        text = (
            f"👤 **THÔNG TIN TÀI KHOẢN FREE FIRE**\n"
            f"➖➖➖➖➖➖➖➖➖➖\n"
            f"🎮 **Tên In-game**: `{result['nickname']}`\n"
            f"🆔 **UID**: `{uid}`\n"
            f"⭐ **Cấp Độ (Level)**: `{result['level']}`\n"
            f"❤️ **Lượt Like**: `{result['likes']}`\n"
            f"🛡️ **Quân Đoàn**: `{result['clan_name']}` (Lv {result['clan_level']})\n"
            f"➖➖➖➖➖➖➖➖➖➖"
        )
        bot.reply_to(message, text, parse_mode="Markdown")
    else:
        err_msg = (
            f"❌ **KHÔNG LẤY ĐƯỢC THÔNG TIN UID `{uid}`**\n\n"
            f"🔍 **Báo lỗi chi tiết:**\n{result}"
        )
        bot.reply_to(message, err_msg, parse_mode="Markdown")

# Đã hỗ trợ thêm các lệnh /buff, /bufflike, /like
@bot.message_handler(commands=['buff', 'bufflike', 'like'])
def handle_buff(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Vui lòng nhập cú pháp: `/buff <UID>` hoặc `/like <UID>`", parse_mode="Markdown")
        return

    uid = args[1]
    bot.reply_to(message, f"🔥 Đang kiểm tra Token và chuẩn bị xả Like vào UID `{uid}`...", parse_mode="Markdown")

    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            raw_tokens = [line.strip() for line in f if line.strip()]
    except Exception:
        raw_tokens = []

    if not raw_tokens:
        raw_tokens, _ = generate_tokens_pool(50)

    if not raw_tokens:
        bot.reply_to(message, "❌ **LỖI:** Không có Token khả dụng! Hãy gõ `/renew` để xem chi tiết lỗi sinh token.", parse_mode="Markdown")
        return

    # Lọc Token Live
    with ThreadPoolExecutor(max_workers=15) as executor:
        live_tokens = [t for t in executor.map(check_token_live, raw_tokens) if t]

    if not live_tokens:
        bot.reply_to(message, f"❌ Tất cả `{len(raw_tokens)}` Token hiện tại đều đã HẾT HẠN hoặc bị chặn! Vui lòng gõ `/renew` để tạo lại.", parse_mode="Markdown")
        return

    # Check trước khi buff
    success_before, before = get_player_profile_detailed(uid, live_tokens[0])
    likes_before = before['likes'] if success_before else "N/A"

    # Bắn like
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = executor.map(lambda t: send_like_request(t, uid), live_tokens)
        success_count = sum(1 for r in results if r)

    # Check sau khi buff
    success_after, after = get_player_profile_detailed(uid, live_tokens[0])
    likes_after = after['likes'] if success_after else "N/A"

    text = (
        f"🎉 **BUFF LIKE HOÀN TẤT!**\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🎮 **Tên**: `{before['nickname'] if success_before else 'N/A'}`\n"
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
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
