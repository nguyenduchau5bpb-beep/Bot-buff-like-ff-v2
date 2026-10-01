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
# 3. LỆNH /START & /HELP (MENU TRỢ GIÚP NÂNG CẤP)
# ====================================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 **HỆ THỐNG BOT FREE FIRE AUTOMATION** 🤖\n\n"
        "Chào mừng bạn! Dưới đây là danh sách các lệnh khả dụng:\n\n"
        "🔍 `/check <UID>` - Kiểm tra thông tin tài khoản (Tên, Level, Like...)\n"
        "👍 `/like <UID>` - Buff lượt thích (Like) cho tài khoản\n\n"
        "💡 *Ví dụ sử dụng:* `/check 17050297973`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# ====================================================
# 4. LỆNH CHECK UID NÂNG CẤP (/check <UID>)
# ====================================================
@bot.message_handler(commands=['check'])
def check_uid(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(
                message, 
                "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVui lòng nhập: `/check <UID>`\n*Ví dụ:* `/check 17050297973`", 
                parse_mode="Markdown"
            )
            return

        uid = args[1].strip()
        if not uid.isdigit():
            bot.reply_to(message, "❌ **LỖI:** UID phải là dãy chữ số!", parse_mode="Markdown")
            return

        # Thông báo trạng thái đang xử lý
        status_msg = bot.reply_to(message, "⏳ *Đang tra cứu dữ liệu từ Garena...*", parse_mode="Markdown")

        url = f"https://free-fire-api-four.vercel.app/info?uid={uid}&region=VN"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **TRA CỨU THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ **Lỗi:** {err_msg}"
            else:
                account_info = data.get("AccountInfo", data)
                nickname = account_info.get("AccountName") or data.get("nickname") or "Không rõ"
                level = account_info.get("AccountLevel") or data.get("level") or "N/A"
                likes = account_info.get("AccountLikes") or data.get("likes") or "N/A"
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
            msg = f"❌ **TRA CỨU THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ **Mã lỗi HTTP:** `{response.status_code}`"

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** Máy chủ phản hồi quá lâu (Timeout). Vui lòng thử lại sau!")
    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

# ====================================================
# 5. LỆNH BUFF LIKE NÂNG CẤP (/like <UID>)
# ====================================================
@bot.message_handler(commands=['like', 'bufflike'])
def buff_like(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(
                message, 
                "⚠ **CÚ PHÁP KHÔNG HỢP LỆ!**\nVui lòng nhập: `/like <UID>`\n*Ví dụ:* `/like 17050297973`", 
                parse_mode="Markdown"
            )
            return

        uid = args[1].strip()
        if not uid.isdigit():
            bot.reply_to(message, "❌ **LỖI:** UID phải là dãy chữ số!", parse_mode="Markdown")
            return

        status_msg = bot.reply_to(message, "⏳ *Đang gửi yêu cầu Buff Like...*", parse_mode="Markdown")

        url = f"https://free-fire-api-four.vercel.app/like?uid={uid}&region=VN&key=FREE"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ **Lỗi:** {err_msg}"
            else:
                msg = (
                    "🎉 **BUFF LIKE THÀNH CÔNG!**\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **UID Được Buff:** `{uid}`\n"
                    "✨ **Trạng thái:** Đã tăng lượt thích thành công!\n"
                    "━━━━━━━━━━━━━━━━━━━━"
                )
        else:
            msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n🆔 **UID:** `{uid}`\n⚠️ **Mã lỗi HTTP:** `{response.status_code}`"

        bot.edit_message_text(msg, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** Máy chủ phản hồi quá lâu (Timeout). Vui lòng thử lại sau!")
    except Exception as e:
        bot.reply_to(message, f"❌ **LỖI HỆ THỐNG:** `{str(e)}`", parse_mode="Markdown")

# ====================================================
# 6. KHỞI CHẠY ĐA LUỒNG BOT VÀ FLASK SERVER
# ====================================================
if __name__ == "__main__":
    # Khởi chạy Flask Server trên luồng phụ (Thread)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🚀 Bot Free Fire Telegram đang chạy...")
    bot.infinity_polling(skip_pending=True)
