import requests
import json

TOKENS_FILE = "tokens.txt"

TOKEN_SOURCES = [
    "https://raw.githubusercontent.com/FreeFireAPI/tokens/main/tokens.txt",
    "https://api-freefire-tokens.vercel.app/get_tokens",
    "https://ff-token-pool.vercel.app/tokens"
]

def check_vn_region(token):
    """Kiểm tra xem Token có thuộc Server Việt Nam (VN) không"""
    try:
        url = "https://clientbp.ggblueshark.com/get_player_personal_info"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19SG Build/RKQ1.201022.002)"
        }
        res = requests.post(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data.get("region") == "VN":
                return True
    except Exception:
        pass
    return False

def fetch_free_tokens():
    collected_tokens = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in TOKEN_SOURCES:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                lines = res.text.splitlines()
                for line in lines:
                    token = line.strip()
                    if token and len(token) > 20 and token not in collected_tokens:
                        # Kiểm tra lọc đúng Token VN
                        if check_vn_region(token):
                            collected_tokens.append(token)
        except Exception:
            continue

    return collected_tokens

def main():
    print("🔄 Đang thu thập và kiểm tra Token Server VN...")
    tokens = fetch_free_tokens()

    if tokens:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            for t in tokens:
                f.write(f"{t}\n")
        print(f"🎉 Đã lưu {len(tokens)} Token VN hợp lệ vào {TOKENS_FILE}")
    else:
        print("⚠️ Không lọc được Token VN nào khả dụng từ nguồn public.")

if __name__ == "__main__":
    main()
