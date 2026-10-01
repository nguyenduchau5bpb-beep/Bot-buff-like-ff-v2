import os
import threading
import requests
from flask import Flask
import telebot

# ====================================================
# 1. CẤU HÌNH FLASK WEB SERVER (DÙNG GIỮ PORT RENDER)
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
# 3. DANH SÁCH API ENDPOINTS (TỰ ĐỘNG XOAY VÒNG DỰ PHÒNG)
# ====================================================
INFO_APIS = [
    "https://api-freefire.vercel.app/info/{uid}?region=VN",
    "https://free-fire-api-four.vercel.app/info?uid={uid}&region=VN",
    "https://ff-api-src.vercel.app/info?uid={uid}&region=VN"
]

LIKE_APIS = [
    "https://api-freefire.vercel.app/like/{uid}?region=VN",
    "https://free-fire-api-four.vercel.app/like?uid={uid}&region=VN&key=FREE",
    "https://ff-api-src.vercel.app/like?uid={uid}&region=VN"
]

# ====================================================
# 4. HÀM XỬ LÝ GỌI API LINH HOẠT (FALLBACK SYSTEM)
# ====================================================
def fetch_api_data(api_list, uid):
    """
    Duyệt qua lần lượt từng URL trong danh sách.
    Nếu URL nào phản hồi thành công (HTTP 200) thì trả về dữ liệu ngay lập tức.
    """
    for api_template in api_list:
        url = api_template.format(uid=uid)
        try:
            response = requests.get(url, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if not ("error" in data or "message" in data and len(data) == 1):
                    return True, data
        except Exception:
            continue  # Nếu lỗi kết nối hoặc timeout, tự động chuyển sang API tiếp theo
    return False, None

# ====================================================
# 5. LỆNH /START & /HELP
# ====================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **HỆ THỐNG BOT FREE FIRE AUTOMATION** 🤖\n\n"
        "Chào mừng bạn! Dưới đây là danh sách các lệnh khả dụng:\n\n"
        "🔍 `/check <UID>` - Kiểm tra thông tin tài khoản\n"
        "👍 `/like <UID>` - Buff lượt thích (Like) cho tài khoản\n\n"
        "💡 *Ví dụ:* `/check 18365419475`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# ====================================================
# 6. LỆNH CHECK UID (/check <UID>)
# ====================================================
@bot.message_handler(commands=['check'])
def check_uid(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(
                message, 
                "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVui lòng nhập: `/check <UID>`\n*Ví dụ:* `/check 18365419475`", 
                parse_mode="Markdown"
            )
            return

        uid = args[1].strip()
        if not uid.isdigit():
            bot.reply_to(message, "❌ **LỖI:** UID phải là dãy chữ số!", parse_mode="Markdown")
            return

        status_msg = bot.reply_to(message, "⏳ *Đang tra cứu dữ liệu (Tự động kết nối server tối ưu)...*", parse_mode="Markdown")

        # Thử gọi danh sách API
        success, data = fetch_api_data(INFO_APIS, uid)

        if success and data:
            account_info = data.get("AccountInfo") or data.get("data") or data
            nickname = account_info.get("AccountName") or account_info.get("nickname") or "Không rõ"
            level = account_info.get("AccountLevel") or account_info.get("level") or "N/A"
            likes = account_info.get("AccountLikes") or account_info.get("likes") or "N/A"
            region = account_info.get("AccountRegion") or "VN"

            msg = (
                "🎮 **THÔNG TIN TÀI KHOẢN FREE FIRE**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **Tên nhân vật:** `{nickname}`\n"
                f"🆔 **UID:** `{uid}`\n"
                f"⭐ **Cấp độ (Level):** `{level}`\n"
                f"👍 **Lượt thích (Likes):** `{likes}`\n"
                f"🌐 **Khu vực:** `{region}`\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            msg = f"❌ **TRA CỨU THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ Tất cả các API server hiện tại đều không phản hồi. Vui lòng thử lại sau!"

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

# ====================================================
# 7. LỆNH BUFF LIKE (/like <UID>)
# ====================================================
@bot.message_handler(commands=['like', 'bufflike'])
def buff_like(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(
                message, 
                "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVui lòng nhập: `/like <UID>`\n*Ví dụ:* `/like 18365419475`", 
                parse_mode="Markdown"
            )
            return

        uid = args[1].strip()
        if not uid.isdigit():
            bot.reply_to(message, "❌ **LỖI:** UID phải là dãy chữ số!", parse_mode="Markdown")
            return

        status_msg = bot.reply_to(message, "⏳ *Đang kết nối Server Buff Like...*", parse_mode="Markdown")

        # Thử gọi danh sách API
        success, data = fetch_api_data(LIKE_APIS, uid)

        if success and data:
            msg = (
                "🎉 **BUFF LIKE THÀNH CÔNG!**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **UID Được Buff:** `{uid}`\n"
                "✨ **Trạng thái:** Đã gửi tim thành công!\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
        else:
            msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ Tất cả các API server hiện tại đều không phản hồi. Vui lòng thử lại sau!"

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

# ====================================================
# 8. KHỞI CHẠY BOT
# ====================================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 Bot Free Fire Telegram đang chạy...")
    bot.infinity_polling(skip_pending=True)
