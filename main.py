import os
import threading
from flask import Flask
import telebot
import requests

# === CẤU HÌNH WEB SERVER FLASK (DÙNG CHO RENDER) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Free Fire đang hoạt động 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# === CẤU HÌNH TOKEN ===
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------
# 1. LỆNH CHECK UID (/check <UID>)
# ----------------------------------------------------
@bot.message_handler(commands=['check'])
def check_uid(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠ **Vui lòng nhập UID!**\nVí dụ: `/check 17050297973`", parse_mode="Markdown")
            return

        uid = args[1]
        url = f"https://free-fire-api-four.vercel.app/info?uid={uid}&region=VN"
        response = requests.get(url, timeout=12)
        status_code = response.status_code

        if status_code == 200:
            data = response.json()
            # Kiểm tra dữ liệu trả về từ API
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** {err_msg}"
            else:
                # Trích xuất thông tin cơ bản
                account_info = data.get("AccountInfo", data)
                nickname = account_info.get("AccountName") or data.get("nickname") or "N/A"
                level = account_info.get("AccountLevel") or data.get("level") or "N/A"
                likes = account_info.get("AccountLikes") or data.get("likes") or "N/A"

                msg = (
                    f"✅ **CHECK THÀNH CÔNG**\n\n"
                    f"**UID:** `{uid}`\n"
                    f"**Tên:** `{nickname}`\n"
                    f"**Level:** `{level}`\n"
                    f"**Lượt thích:** `{likes}`"
                )
        else:
            msg = f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}\n**Lỗi:** Không lấy được thông tin"

        bot.reply_to(message, msg, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** Yêu cầu quá thời gian (Timeout)")
    except Exception as e:
        bot.reply_to(message, f"❌ **CHECK THẤT BẠI**\n\n**Lỗi hệ thống:** {str(e)}")

# ----------------------------------------------------
# 2. LỆNH BUFF LIKE (/like <UID> hoặc /bufflike <UID>)
# ----------------------------------------------------
@bot.message_handler(commands=['like', 'bufflike'])
def buff_like(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠ **Vui lòng nhập UID!**\nVí dụ: `/like 17050297973`", parse_mode="Markdown")
            return

        uid = args[1]
        url = f"https://free-fire-api-four.vercel.app/like?uid={uid}&region=VN&key=FREE"
        response = requests.get(url, timeout=12)
        status_code = response.status_code

        if status_code == 200:
            data = response.json()
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** {err_msg}"
            else:
                msg = f"✅ **BUFF LIKE THÀNH CÔNG**\n\n**UID:** `{uid}`\n**Kết quả:** Đã gửi tim thành công!"
        else:
            msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}"

        bot.reply_to(message, msg, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** Yêu cầu quá thời gian (Timeout)")
    except Exception as e:
        bot.reply_to(message, f"❌ **BUFF LIKE THẤT BẠI**\n\n**Lỗi hệ thống:** {str(e)}")

# ----------------------------------------------------
# KHỞI CHẠY BOT VÀ FLASK SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Bot Telegram và Flask Server đang hoạt động...")
    bot.infinity_polling()
