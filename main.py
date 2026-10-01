import os
import threading
from flask import Flask
import telebot
import requests

# === CẤU HÌNH WEB SERVER FLASK ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Free Fire đang hoạt động 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# === CẤU HÌNH TOKEN ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
FF_TOKEN = os.getenv("FF_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# ----------------------------------------------------
# 1. LỆNH CHECK UID (/check <UID>)
# ----------------------------------------------------
@bot.message_handler(commands=['check'])
def check_uid(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠ **Vui lòng nhập UID!**\nVí dụ: `/check 18365419475`", parse_mode="Markdown")
            return

        uid = args[1]
        headers = {
            "Authorization": f"Bearer {FF_TOKEN}",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)",
            "Content-Type": "application/json"
        }
        
        url = f"https://clientbp.ggblueshark.com/get_player_info?uid={uid}"
        response = requests.get(url, headers=headers, timeout=12)
        status_code = response.status_code

        if status_code == 200:
            data = response.json()
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}\n**Lỗi:** {err_msg}"
            else:
                msg = (
                    f"✅ **CHECK THÀNH CÔNG**\n\n"
                    f"**UID:** `{uid}`\n"
                    f"**Tên:** {data.get('nickname', 'N/A')}\n"
                    f"**Level:** {data.get('level', 'N/A')}\n"
                    f"**Likes:** {data.get('likes', 'N/A')}"
                )
        else:
            try:
                err_json = response.json()
                err_detail = err_json.get("message") or err_json.get("error") or response.text
            except Exception:
                err_detail = response.text or "Lỗi không xác định"

            msg = f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}\n**Lỗi:** {err_detail}"

        bot.reply_to(message, msg, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **CHECK THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** Request Timeout")
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
            bot.reply_to(message, "⚠ **Vui lòng nhập UID!**\nVí dụ: `/like 18365419475`", parse_mode="Markdown")
            return

        uid = args[1]
        headers = {
            "Authorization": f"Bearer {FF_TOKEN}",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)",
            "Content-Type": "application/json"
        }
        
        url = f"https://clientbp.ggblueshark.com/like_player?uid={uid}"
        response = requests.post(url, headers=headers, timeout=12)
        status_code = response.status_code

        if status_code == 200:
            data = response.json()
            if "error" in data or "message" in data:
                err_msg = data.get("error") or data.get("message")
                msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}\n**Lỗi:** {err_msg}"
            else:
                msg = f"✅ **BUFF LIKE THÀNH CÔNG**\n\n**UID:** `{uid}`\n**Trạng thái:** Đã gửi tim thành công!"
        else:
            try:
                err_json = response.json()
                err_detail = err_json.get("message") or err_json.get("error") or response.text
            except Exception:
                err_detail = response.text or "Lỗi không xác định"

            msg = f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Status:** {status_code}\n**Lỗi:** {err_detail}"

        bot.reply_to(message, msg, parse_mode="Markdown")

    except requests.exceptions.Timeout:
        bot.reply_to(message, f"❌ **BUFF LIKE THẤT BẠI**\n\n**UID:** `{uid}`\n**Lỗi:** Request Timeout")
    except Exception as e:
        bot.reply_to(message, f"❌ **BUFF LIKE THẤT BẠI**\n\n**Lỗi hệ thống:** {str(e)}")

# ----------------------------------------------------
# KHỞI CHẠY BOT VÀ FLASK SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Bot Telegram và Flask Web Server đang hoạt động...")
    bot.infinity_polling()
 
