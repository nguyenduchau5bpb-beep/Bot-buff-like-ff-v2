import os
import threading
import requests
from flask import Flask
import telebot

# ====================================================
# 1. CẤU HÌNH FLASK WEB SERVER (GIỮ PORT RENDER 24/7)
# ====================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "<h3>Bot Free Fire Telegram đang hoạt động 24/7!</h3>", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ====================================================
# 2. KHỞI TẠO BOT TELEGRAM
# ====================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("⚠ CẢNH BÁO: Chưa cấu hình biến môi trường BOT_TOKEN!")

bot = telebot.TeleBot(BOT_TOKEN)

# ====================================================
# 3. DANH SÁCH API CHECK THÔNG TIN DỰ PHÒNG
# ====================================================
INFO_APIS = [
    "https://api-freefire.vercel.app/info/{uid}?region=VN",
    "https://region-info-ff.vercel.app/info?uid={uid}&region=VN",
    "https://free-fire-api-garena.vercel.app/api/info/{uid}"
]

def fetch_info(uid):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for api_template in INFO_APIS:
        url = api_template.format(uid=uid)
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if not ("error" in data or "message" in data and len(data) == 1):
                    return True, data
        except Exception:
            continue
    return False, None

# ====================================================
# 4. HÀM BUFF LIKE TỪ POOL TOKEN (FILE tokens.txt)
# ====================================================
def buff_like_with_tokens(target_uid):
    token_file = "tokens.txt"
    if not os.path.exists(token_file):
        return False, "Không tìm thấy file tokens.txt! Hệ thống đang chờ GitHub Actions tạo mới."

    with open(token_file, "r", encoding="utf-8") as f:
        tokens = [line.strip() for line in f if line.strip()]

    if not tokens:
        return False, "File tokens.txt hiện đang trống!"

    success_count = 0
    for token in tokens:
        try:
            url = f"https://clientbp.ggblueshark.com/like_player?uid={target_uid}"
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)",
                "Content-Type": "application/json"
            }
            res = requests.post(url, headers=headers, timeout=5)
            if res.status_code == 200:
                success_count += 1
        except Exception:
            continue

    if success_count > 0:
        return True, f"Đã gửi thành công {success_count}/{len(tokens)} tim!"
    return False, "Tất cả Token trong file đều không hợp lệ hoặc đã hết hạn."

# ====================================================
# 5. LỆNH BOT TELEGRAM (/start, /check, /like)
# ====================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **HỆ THỐNG BOT FREE FIRE AUTOMATION** 🤖\n\n"
        "🔍 `/check <UID>` - Kiểm tra thông tin tài khoản\n"
        "👍 `/like <UID>` - Buff lượt thích (Like) cho tài khoản\n\n"
        "💡 *Ví dụ:* `/check 18365419475`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check_uid(message):
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVí dụ: `/check 18365419475`", parse_mode="Markdown")
            return

        uid = args[1].strip()
        status_msg = bot.reply_to(message, "⏳ *Đang tra cứu dữ liệu...*", parse_mode="Markdown")

        success, data = fetch_info(uid)
        if success and data:
            account_info = data.get("AccountInfo") or data.get("data") or data
            nickname = account_info.get("AccountName") or account_info.get("nickname") or "Không rõ"
            level = account_info.get("AccountLevel") or account_info.get("level") or "N/A"
            likes = account_info.get("AccountLikes") or account_info.get("likes") or "N/A"

            msg = (
                "🎮 **THÔNG TIN TÀI KHOẢN FREE FIRE**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Tên nhân vật:** `{nickname}`\n"
                f"🆔 **UID:** `{uid}`\n"
                f"⭐ **Cấp độ (Level):** `{level}`\n"
                f"👍 **Lượt thích (Likes):** `{likes}`\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            msg = f"❌ **TRA CỨU THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ Các API server hiện tại không phản hồi."

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

@bot.message_handler(commands=['like', 'bufflike'])
def buff_like(message):
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            bot.reply_to(message, "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVí dụ: `/like 18365419475`", parse_mode="Markdown")
            return

        uid = args[1].strip()
        status_msg = bot.reply_to(message, "⏳ *Đang tiến hành Buff Like từ Token Pool...*", parse_mode="Markdown")

        success, result_msg = buff_like_with_tokens(uid)

        if success:
            msg = (
                "🎉 **BUFF LIKE THÀNH CÔNG!**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **UID Được Buff:** `{uid}`\n"
                f"✨ **Kết quả:** {result_msg}\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ **Chi tiết:** {result_msg}"

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

# ====================================================
# 6. KHỞI CHẠY ĐA LUỒNG
# ====================================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 Bot Free Fire Telegram đang chạy...")
    bot.infinity_polling(skip_pending=True)
