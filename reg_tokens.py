import requests
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

TOKENS_FILE = "tokens.txt"
GARENA_GUEST_URL = "https://100067.connect.garenanow.com/guest/login"

def create_ff_guest_token(_):
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

def main():
    print("🚀 Đang khởi tạo Token Guest tự động từ Garena...")
    tokens = set()
    target_count = 100  # Sinh 100 token cho mỗi lượt

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(create_ff_guest_token, range(target_count))
        for token in results:
            if token:
                tokens.add(token)

    if tokens:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            for t in tokens:
                f.write(f"{t}\n")
        print(f"✅ Thành công: Lưu {len(tokens)} Token mới vào {TOKENS_FILE}")
    else:
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            f.write("")
        print("❌ Không tạo được token mới.")

if __name__ == "__main__":
    main()
