#!/usr/bin/env python3
"""
Winner's Horse Korean Localization ROM Patcher

Changes:
1. Replace tile data at VRAM 0x21-0xCD with Korean character glyphs
2. Modify text renderer to use direct tile indexing (skip katakana processing)
3. Replace Japanese text strings with Korean-encoded equivalents
"""
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')
from pathlib import Path
import shutil

ROM_PATH = '/home/user/gb_winners_horse/Winners_Horse_Japan.gb'
OUT_PATH = '/home/user/gb_winners_horse/Winners_Horse_Korean.gb'
TILES_BIN = '/home/user/gb_winners_horse/tiles/korean_tiles.bin'

# ─── Korean character set (sorted, same as extract_tiles.py) ───────────────
TRANSLATIONS_SRC = [
    "사쓰키상","천황상봄가을","야스다기념","일본더비","다카라즈카기념","국화상",
    "엘리자베스여왕배","마일챔피언십","재팬컵","아사히배세스테이크스",
    "스프린터즈","아리마기념","오카쇼","오크스","한신","요코에컵","더비트라이얼",
    "미승리전","게이세이배","닛케이신춘","신마전","다이아몬드",
    "도쿄신문배","교토통신","기사라기","월핸디캡","메구로기념","교토기념",
    "호치배야요이상","페가수스","나카야마기념","한신대상전","마이니치배",
    "닛케이상","산케이오사카배","세특별","게이한배","한큐배","엡솜컵",
    "다카마쓰노미야배","삿포로","니가타","고쿠라","센토르","고베신문배",
    "하코다테","마이니치왕관","교토대상전","교토신문배","스완","네기시",
    "게이머","대상기념","크리스탈컵","가쓰오","나루오기념","윈터","스테이어즈",
    "주쿄","후쿠시마",
    "위와같이확정되었습니다","기록이없습니다","성적전적승","상금",
    "맑음흐림비폭풍잔디","두수성별부담중량","기수실적코스거리적성",
    "중마장적성등급최근과거조교상태마체중휴양마방",
    "두수는마장상태는거리는얼마나됩니까부담중량은",
    "어느항목을수정하시겠습니까성별은",
    "마장상태적성마체중증감미승리",
    "도주선행차입추입핸디캡연승",
    "은퇴까지년남았습니다밖에않았",
    "게이한큐탈퇴특팬솜쇼쿠큐프피",
]

all_chars = set()
for text in TRANSLATIONS_SRC:
    for ch in text:
        if '가' <= ch <= '힣':
            all_chars.add(ch)
KOREAN_CHARS = sorted(all_chars)
CHAR_TO_IDX = {ch: i for i, ch in enumerate(KOREAN_CHARS)}

# byte encoding: Korean char index i → ROM byte value 0x21 + i
KOREAN_BYTE_BASE = 0x21

def encode_kr(text: str) -> bytes:
    """Encode a Korean string into ROM byte values."""
    result = []
    for ch in text:
        if '가' <= ch <= '힣':
            idx = CHAR_TO_IDX.get(ch)
            if idx is None:
                raise ValueError(f"Korean char '{ch}' not in char set!")
            result.append(KOREAN_BYTE_BASE + idx)
        # skip spaces and punctuation in Korean text for now
    return bytes(result)

def center_pad(content: bytes, width: int, pad_byte: int = 0x20) -> bytes:
    """Center content in a fixed-width field, padded with pad_byte."""
    content = content[:width]
    left = (width - len(content)) // 2
    right = width - len(content) - left
    return bytes([pad_byte] * left) + content + bytes([pad_byte] * right)

# ─── Text translation table ─────────────────────────────────────────────────
# Format: (file_offset, korean_text, slot_type)
# slot_type: 'race22' = 22-byte fixed slot, 'var' = variable null-terminated

PATCH_TABLE = [
    # ── Race names (22-byte fixed slots: 0x03 + 20 centered chars + 0x00) ──
    # Bank 1 race names
    (0x04F57, "사쓰키상",       'race22'),   # サツキショウ
    (0x04F6D, "천황상봄",       'race22'),   # テンノウショウ(ハル)
    (0x04F83, "야스다기념",     'race22'),   # ヤスダキネン
    (0x04F99, "일본더비",       'race22'),   # ダービー
    (0x04FAF, "다카라즈카기념", 'race22'),   # タカラヅカキネン
    (0x04FC5, "천황상가을",     'race22'),   # テンノウショウ(アキ)
    (0x04FDB, "국화상",         'race22'),   # キッカショウ
    (0x04FF1, "마일챔피언십",   'race22'),   # マイルCS
    (0x05007, "재팬컵",         'race22'),   # ジャパンカップ
    (0x0501D, "요코에컵",       'race22'),   # ヨコエカップ
    (0x05033, "아사히배세스테이크스", 'race22'),  # アサヒ杯3歳S
    (0x05049, "스프린터즈",     'race22'),   # スプリンターズS
    (0x0505F, "아리마기념",     'race22'),   # アリマキネン

    # Bank 2 race names
    (0x0B45A, "오카쇼",         'race22'),   # オウカショウ
    (0x0B49A, "오크스",         'race22'),   # オークス
    (0x0B4EA, "엘리자베스여왕배", 'race22'), # エリザベス女王杯

    # Bank 6 race names
    (0x1814B, "미승리전",       'race22'),   # ミショウリセン
    (0x18159, "게이세이배",     'race22'),   # ケイセイ杯
    (0x18175, "게이머",         'race22'),   # ゲーマーS
    (0x18199, "닛케이신춘배",   'race22'),   # ニッケイシンシュン杯
    (0x181AA, "신마전",         'race22'),   # シンバセン
    (0x181B7, "다이아몬드",     'race22'),   # ダイヤモンドS
    (0x181C7, "가쓰오",         'race22'),   # カツオS
    (0x181D2, "도쿄신문배",     'race22'),   # トウキョウシンブン杯
    (0x181EF, "교토통신배",     'race22'),   # キョウトツウシン杯4歳S
    (0x18204, "기사라기상",     'race22'),   # キサラギショウ
    (0x1822E, "메구로기념",     'race22'),   # メグロキネン
    (0x1823C, "교토기념",       'race22'),   # キョウトキネン
    (0x18276, "호치배야요이상", 'race22'),   # ホウチ杯ヤヨイショウ
    (0x18287, "페가수스",       'race22'),   # ペガサスS
    (0x182A2, "나카야마기념",   'race22'),   # ナカヤマキネン
    (0x182B0, "한신대상전",     'race22'),   # ハンシンダイショウテン
    (0x182FB, "대상기념",       'race22'),   # タイショウキネン
    (0x18325, "마이니치배",     'race22'),   # マイニチ杯
    (0x1833C, "닛케이상",       'race22'),   # ニッケイショウ
    (0x1834A, "산케이오사카배", 'race22'),   # サンケイオオサカ杯
    (0x18368, "크리스탈컵",     'race22'),   # クリスタルC
    (0x18422, "게이한배",       'race22'),   # ケイハン杯
    (0x1846E, "한큐배",         'race22'),   # ハンキュウ杯
    (0x18488, "엡솜컵",         'race22'),   # エプソムC
    (0x18504, "다카마쓰노미야배", 'race22'), # タカマツミヤ杯
    (0x18563, "삿포로세스테이크스", 'race22'), # サッポロ3歳S
    (0x185EA, "니가타세스테이크스", 'race22'), # ニイガタ3歳S
    (0x185F9, "고쿠라세스테이크스", 'race22'), # コクラ3歳S
    (0x18626, "센토르",         'race22'),   # セントウルS
    (0x1868B, "고베신문배",     'race22'),   # コウベシンブン杯
    (0x1869C, "하코다테세스테이크스", 'race22'), # ハコダテ3歳S
    (0x186AB, "마이니치왕관",   'race22'),   # マイニチオウカン
    (0x186BA, "교토대상전",     'race22'),   # キョウトダイショウテン
    (0x186DA, "교토신문배",     'race22'),   # キョウトシンブン杯
    (0x18715, "스완",           'race22'),   # スワンS
    (0x1873E, "네기시",         'race22'),   # ネギシS
    (0x187A4, "마일챔피언십",   'race22'),   # マイルチャンピオンシップ
    (0x187D5, "요코에컵",       'race22'),   # ヨコエ CUP
    (0x1880A, "스테이어즈",     'race22'),   # ステイヤーズS
    (0x18827, "나루오기념",     'race22'),   # ナルオキネン
    (0x18856, "윈터",           'race22'),   # ウインターS
    (0x187A4, "마일챔피언십",   'race22'),   # duplicate (see above)

    # ── Racecourse names (8-byte slots) ─────────────────────────────────────
    (0x0B65B, "한신",   'var'),    # ハンシン
    (0x0B663, "주쿄",   'var'),    # チュウキョウ
    (0x0B66B, "교토",   'var'),    # キョウト
    (0x0B673, "삿포로", 'var'),    # サッポロ
    (0x0B67B, "하코다테", 'var'),  # ハコダテ
    (0x0B683, "후쿠시마", 'var'),  # フクシマ
    (0x0B68B, "니가타", 'var'),    # ニイガタ
    (0x0B693, "고쿠라", 'var'),    # コクラ

    # ── UI/Dialogue strings ──────────────────────────────────────────────────
    # "위와 같이 확정되었습니다" - var length
    (0x040EE, "위와같이확정되었습니다", 'var'),

    # "기록이 없습니다" - var
    (0x043DF, "기록이없습니다", 'var'),

    # UI labels (stat screen)
    (0x05075, "성적전적승", 'var'),   # セイセキ セン ショウ
    (0x05088, "상금",       'var'),   # ショウキン

    # Weather labels
    (0x05E26, "맑음", 'var'),   # ハレ
    (0x05E2A, "흐림", 'var'),   # クモリ
    (0x05E2F, "비",   'var'),   # アメ
    (0x05E33, "폭풍", 'var'),   # アラシ
    (0x05E4F, "잔디", 'var'),   # クサ (with parens in JP)

    # Horse info labels (Bank 2)
    (0x0B55A, "두수는",       'var'),  # トウスウハ?
    (0x0B5D1, "마장상태는",   'var'),  # ババジョウタイハ?
    (0x0B69B, "거리는얼마나됩니까", 'var'),  # キョリハドノクライデスカ?
    (0x0B72E, "부담중량은",   'var'),  # フタンジュウリョウハ?

    # Stat label strings (Bank 2, 16-byte slots)
    (0x0B7A0, "두수",       'var'),   # トウメ
    (0x0B7B5, "성별",       'var'),   # セイベツ
    (0x0B7C5, "부담중량",   'var'),   # フタンジュウリョウ
    (0x0B7D5, "기수실적",   'var'),   # キシュノジッセキ
    (0x0B7E5, "코스",       'var'),   # コース
    (0x0B7F5, "거리적성",   'var'),   # キョリテキセイ
    (0x0B805, "중마장적성", 'var'),   # オモババテキセイ
    (0x0B815, "등급",       'var'),   # カクヅケ
    (0x0B825, "최근성적",   'var'),   # サイキンノセイセキ
    (0x0B835, "과거실적",   'var'),   # カコノジッセキ
    (0x0B845, "조교상태",   'var'),   # チョウキョウジョウタイ
    (0x0B855, "마체중",     'var'),   # バタイジュウ
    (0x0B865, "휴양",       'var'),   # キュウヨウ
    (0x0B875, "마방",       'var'),   # キャクシツ
    (0x0B885, "어느항목을수정하시겠습니까", 'var'),  # ドノコウモクヲ...
    (0x0B972, "성별은",     'var'),   # セイベツハ?

    # Running style (Bank 2)
    (0x0BA41, "도주", 'var'),   # ニゲ
    (0x0BA47, "선행", 'var'),   # センコウ
    (0x0BA4D, "차입", 'var'),   # サシ
    (0x0BA53, "추입", 'var'),   # オイコミ

    (0x0BA8D, "마장상태적성",   'var'),  # ババジョウタイテキセイ
    (0x0BAC6, "마체중증감",     'var'),  # バタイジュウノゾウゲン
    (0x0BCAC, "핸디캡연승",     'var'),  # ハンデ連勝
    (0x18782, "미승리",         'var'),  # ミショウリ (Bank 6)

    # Retirement messages (Bank 7)
    (0x1E9AA, "은퇴까지년남았습니다", 'var'),  # 引退まで4年ある
    (0x1E9BA, "은퇴까지년남았습니다", 'var'),  # 引退まで3年ある
    (0x1E9CA, "은퇴까지년밖에않았습니다", 'var'),  # 引退まで2年しかない
]


def patch_string(rom: bytearray, offset: int, korean_text: str, slot_type: str):
    """Patch one string in ROM with Korean-encoded replacement."""
    encoded = encode_kr(korean_text)

    if slot_type == 'race22':
        # 22-byte fixed slot: [03][20 chars centered][00]
        body = center_pad(encoded, 20, 0x20)
        new_bytes = bytes([0x03]) + body + bytes([0x00])
        if len(new_bytes) != 22:
            raise ValueError(f"race22 slot wrong length: {len(new_bytes)}")
        rom[offset:offset+22] = new_bytes

    elif slot_type == 'var':
        # Variable: find end of original string (null terminator)
        end = offset
        while end < offset + 64 and rom[end] != 0x00:
            end += 1
        orig_len = end - offset  # not counting the 0x00

        # Build: keep original control code (0x01-0x03) + space prefix if any
        ctrl = rom[offset] if rom[offset] <= 0x03 else None
        if ctrl is not None:
            # Keep leading spaces up to non-space content
            i = offset + 1
            spaces_before = []
            while i < end and rom[i] == 0x20:
                spaces_before.append(0x20)
                i += 1

            new_body = bytes([ctrl]) + bytes(spaces_before) + encoded
        else:
            new_body = encoded

        # Pad with spaces to match original length, then terminate
        if len(new_body) < orig_len:
            new_body = new_body + bytes([0x20] * (orig_len - len(new_body)))
        elif len(new_body) > orig_len:
            new_body = new_body[:orig_len]  # truncate to fit

        new_bytes = new_body + bytes([0x00])
        rom[offset:offset+len(new_bytes)] = new_bytes

    return encoded


def main():
    print("=== Winner's Horse Korean Localization Patcher ===\n")

    # Load ROM
    with open(ROM_PATH, 'rb') as f:
        rom = bytearray(f.read())
    print(f"ROM loaded: {len(rom)} bytes")

    # ── 1. Replace Korean tile data ────────────────────────────────────────
    TILE_TABLE = 0x10090   # bank 4 tile data: 256 tiles × 16 bytes
    KOREAN_TILE_START = TILE_TABLE + KOREAN_BYTE_BASE * 16  # = 0x102A0
    NUM_KOREAN_TILES = len(KOREAN_CHARS)

    with open(TILES_BIN, 'rb') as f:
        korean_tile_data = f.read()

    assert len(korean_tile_data) == NUM_KOREAN_TILES * 16, \
        f"Expected {NUM_KOREAN_TILES*16} bytes, got {len(korean_tile_data)}"

    rom[KOREAN_TILE_START : KOREAN_TILE_START + len(korean_tile_data)] = korean_tile_data
    print(f"[1] Korean tiles written: {NUM_KOREAN_TILES} tiles at file 0x{KOREAN_TILE_START:05X}")

    # ── 2. Modify text renderer ────────────────────────────────────────────
    # At file 0x15C6: change FE A1 (CP $A1) to 18 1C (JR +28)
    # This skips all katakana processing → ALL bytes use direct tile indexing
    assert rom[0x15C6] == 0xFE and rom[0x15C7] == 0xA1, \
        f"Text renderer bytes mismatch at 0x15C6: {rom[0x15C6]:02X} {rom[0x15C7]:02X}"
    rom[0x15C6] = 0x18  # JR
    rom[0x15C7] = 0x1C  # offset +28 (→ 0x15E4)
    print(f"[2] Text renderer patched at 0x15C6: JR +28 (skip katakana processing)")

    # ── 3. Also update katakana tile base writes so they don't interfere ───
    # The writes to RAM $C4CE (LD ($C4CE), A [A=0xE0]) are now irrelevant
    # since we bypass the katakana path, but keep them for safety.
    print(f"[3] Katakana base writes left unchanged (now unreachable code path)")

    # ── 4. Replace text strings ────────────────────────────────────────────
    patched = 0
    errors = []
    seen_offsets = set()

    for entry in PATCH_TABLE:
        offset, korean_text, slot_type = entry
        if offset in seen_offsets:
            continue
        seen_offsets.add(offset)

        try:
            encoded = patch_string(rom, offset, korean_text, slot_type)
            patched += 1
            kr_bytes = ' '.join(f'{b:02X}' for b in encoded)
            print(f"  [OK] 0x{offset:05X}: '{korean_text}' → {kr_bytes}")
        except Exception as e:
            errors.append((offset, korean_text, str(e)))
            print(f"  [ERR] 0x{offset:05X}: '{korean_text}': {e}")

    print(f"\n[4] Text strings patched: {patched} OK, {len(errors)} errors")

    # ── 5. Write output ROM ────────────────────────────────────────────────
    with open(OUT_PATH, 'wb') as f:
        f.write(rom)
    print(f"\n[5] Output ROM written: {OUT_PATH}")

    # ── Verify: Show sample string in patched ROM ──────────────────────────
    print("\n=== Verification ===")
    print(f"  0x04F57 raw: {bytes(rom[0x04F57:0x04F57+22]).hex()}")
    print(f"  Tile 0x21 (Korean '가'): {bytes(rom[TILE_TABLE + 0x21*16 : TILE_TABLE + 0x21*16+4]).hex()}")
    print(f"  Text renderer 0x15C6: {rom[0x15C6]:02X} {rom[0x15C7]:02X}")


if __name__ == '__main__':
    main()
