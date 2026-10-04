import requests
from concurrent.futures import ThreadPoolExecutor

TOKENS_FILE = "tokens.txt"

# --- 1. HÀM CHECK CHI TIẾT THÔNG TIN ACC ACC FF (LEVEL, LIKE, QUÂN ĐOÀN...) ---
def check_ff_profile(target_uid, token, region="VN"):
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
                "name": acc.get("Nickname", "N/A"),
                "level": acc.get("Level", 0),
                "likes": acc.get("Likes", 0),
                "exp": acc.get("Exp", 0),
                "clan_name": clan.get("ClanName", "Chưa vào quân đoàn"),
                "clan_level": clan.get("ClanLevel", 0)
            }
    except Exception:
        pass
    return None

# --- 2. HÀM CHECK TOKEN SỐNG (LIVE CHECK) ---
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

# --- 3. HÀM GỬI THẢ TIM ---
def send_like(token, target_uid, region="VN"):
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

# --- 4. HÀM XỬ LÝ CHÍNH ---
def process_buff(target_uid, region="VN"):
    # Bước A: Đọc danh sách Token
    try:
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            raw_tokens = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Chưa có file tokens.txt")
        return

    if not raw_tokens:
        print("⚠️ File tokens.txt đang trống!")
        return

    # Bước B: Lọc Token Sống
    print(f"🔍 [1/3] Đang lọc {len(raw_tokens)} Token...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        live_tokens = [t for t in executor.map(check_token_live, raw_tokens) if t]

    print(f"✅ Phát hiện {len(live_tokens)} Token SỐNG sẵn sàng!")
    if not live_tokens:
        print("❌ Không có Token nào sống để buff.")
        return

    # Bước C: Check thông tin UID trước khi Buff
    profile_before = check_ff_profile(target_uid, live_tokens[0], region)
    if profile_before:
        print("\n================ THÔNG TIN UID TARGET ================")
        print(f"🎮 Tên Nhân Vật : {profile_before['name']}")
        print(f"⭐ Cấp Độ (Level): {profile_before['level']}")
        print(f"❤️ Like Hiện Tại : {profile_before['likes']}")
        print(f"🛡️ Quân Đoàn     : {profile_before['clan_name']} (Lv {profile_before['clan_level']})")
        print("======================================================")

    # Bước D: Xả Like Đồng Loạt
    print(f"\n🔥 [2/3] Đang bắn đồng loạt {len(live_tokens)} LIKE vào UID {target_uid}...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(lambda t: send_like(t, target_uid, region), live_tokens)
        success = sum(1 for r in results if r)

    # Bước E: Kiểm tra kết quả sau khi Buff
    profile_after = check_ff_profile(target_uid, live_tokens[0], region)
    likes_after = profile_after['likes'] if profile_after else "N/A"
    
    print(f"\n🎉 [3/3] HOÀN TẤT! Bắn thành công +{success} LIKE!")
    print(f"📊 Like mới của UID {target_uid}: {likes_after}")

if __name__ == "__main__":
    UID_TEST = "123456789" # Thay UID cần test vào đây
    process_buff(UID_TEST, region="VN")
