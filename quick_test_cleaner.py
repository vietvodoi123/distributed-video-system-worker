# quick_test_cleaner.py
# File test nhanh 2 lớp lọc: Lớp 1 (Tiếng Trung / Crawl) và Lớp 2 (Tiếng Việt / Translate)

import sys
from shared.text.cleaners.cn_cleaner import clean_cn_content
from shared.runtime.executors.translation.translate_text_excutor import (
    filter_corrupted_translation_lines,
)

SAMPLE_CN_TEXT = """“叮鈴鈴……”鄭玉龍本想請王野吃飯，結果話還沒說完，手機就響了起來。
“爸，怎麼了？”
⑻ЬＯOｋ．соｍ
“好，我馬上回去。”

轟！

   讀小說上天天看小說，𝒕𝒕𝒌.𝒕𝒘超省心

  柳天雄身上恐怖的靈力涌動，逼迫的柳如煙，柳飛龍兩人，齊齊後退到了三米開外。

老舊小區里，一個年輕人正在熬夜玩手機。
街角還有個攤子，攤主扯著嗓子喊：“賣白菜，地里剛摘的白菜！”
⑧вОΟｋ.Ｃоｍ
他扶著墻走到街頭，發現今天街上特別熱鬧。
【記住本站域名 天天看小說體驗佳，𝘵𝘵𝘬.𝘵𝘸超讚 】
看書首選天天看小說，𝓽𝓽𝓴.𝓽𝔀超給力
（由於緩存原因，請用戶直接瀏覽器訪問 天天看小說超貼心，𝙩𝘵𝙠.𝙩𝙬等你讀 網站，觀看最快的章節更新）
⑧bοоК．ｃＯm
⒏ｂoОК.CΟｍ
一條橫幅簡單粗暴：“仙門納新，測靈根，入選者賞銀五十兩。”"""

SAMPLE_TRANSLATED_TEXT = """Góc phố còn có một quầy hàng, chủ sạp hét lớn: “Bán cải trắng, rau trắng vừa hái trên đất!”
8<0xD0><0xB2><0xD0><0x9E><0xCE><0x9F>k.C<0xD0><0xBE>m
Hắn vịn tường đi ra đường phố, phát hiện hôm nay trên phố đặc biệt náo nhiệt.
Một tấm biểu ngữ đơn giản thô bạo: "Tiên môn nạp mới, đo linh căn, người được chọn thưởng năm mươi lượng bạc."
8book.com
Ánh mắt Diệp Du trong nháy mắt liền sáng lên."""


def test_layer_1_cn(text: str):
    print("=" * 60)
    print(" [LỚP 1] TEST TIẾNG TRUNG (CRAWL / PREPROCESS)")
    print("=" * 60)
    print("--- [TRƯỚC KHI LỌC] ---")
    print(text)
    print("\n--- [SAU KHI LỌC] ---")
    cleaned = clean_cn_content(text)
    print(cleaned)
    print("=" * 60)
    return cleaned


def test_layer_2_translated(text: str):
    print("=" * 60)
    print(" [LỚP 2] TEST BẢN DỊCH (TRANSLATE - BẮT '><' VÀ BYTE RÁC)")
    print("=" * 60)
    print("--- [TRƯỚC KHI LỌC] ---")
    print(text)
    print("\n--- [SAU KHI LỌC] ---")
    cleaned = filter_corrupted_translation_lines(text)
    print(cleaned)
    print("=" * 60)
    return cleaned


def interactive_menu():
    print("\n" + "#" * 60)
    print(" CHƯƠNG TRÌNH KIỂM TRA BỘ LỌC TÊN MIỀN & RÁC CRAWL / TRANSLATE")
    print("#" * 60)
    print("1. Chạy test mẫu mặc định (Cả 2 lớp Lớp 1 & Lớp 2)")
    print("2. Nhập đoạn text tiếng Trung tùy ý để test Lớp 1 (Crawl)")
    print("3. Nhập đoạn text bản dịch tùy ý để test Lớp 2 (Translate)")
    print("4. Thoát")
    print("-" * 60)

    try:
        choice = input("Chọn (1-4) [Mặc định: 1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice in ("", "1"):
        test_layer_1_cn(SAMPLE_CN_TEXT)
        print("\n")
        test_layer_2_translated(SAMPLE_TRANSLATED_TEXT)
    elif choice == "2":
        print("\nNhập/dán đoạn text tiếng Trung (Gõ 'END' trên dòng mới để kết thúc):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == "END":
                break
            lines.append(line)
        user_text = "\n".join(lines)
        test_layer_1_cn(user_text)
    elif choice == "3":
        print("\nNhập/dán đoạn text bản dịch (Gõ 'END' trên dòng mới để kết thúc):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == "END":
                break
            lines.append(line)
        user_text = "\n".join(lines)
        test_layer_2_translated(user_text)
    else:
        print("Tạm biệt!")


if __name__ == "__main__":
    interactive_menu()
