#!/usr/bin/env python3
"""
Winner's Horse 한글화 - 한글 폰트 타일 추출기
갈무리M[고딕,8x8] TTF → Game Boy 2BPP 타일 형식
"""
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

FONT_PATH = '/home/user/gb_winners_horse/korean_8x8.ttf'
OUT_DIR   = Path('/home/user/gb_winners_horse/tiles')
OUT_DIR.mkdir(exist_ok=True)

# 번역에 필요한 모든 한글 문자
TRANSLATIONS = [
    # 경주명
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
    # 경마장
    "주쿄","후쿠시마",
    # UI
    "위와같이확정되었습니다","기록이없습니다","성적전적승","상금",
    "맑음흐림비폭풍잔디","두수성별부담중량","기수실적코스거리적성",
    "중마장적성등급최근과거조교상태마체중휴양마방",
    "두수는마장상태는거리는얼마나됩니까부담중량은",
    "어느항목을수정하시겠습니까성별은",
    "마장상태적성마체중증감미승리",
    "도주선행차입추입핸디캡연승",
    "은퇴까지년남았습니다밖에않았",
    "게이한큐탈퇴특팬솜쇼쿠큐프피",
    # 코스 설명 (새 문자)
    "평탄해직긴파워반너좌회내모안쪽유",
]

# 고유 한글 문자 수집
all_chars = set()
for text in TRANSLATIONS:
    for ch in text:
        if '가' <= ch <= '힣':
            all_chars.add(ch)

KOREAN_CHARS = sorted(all_chars)
print(f"총 고유 한글 문자: {len(KOREAN_CHARS)}자")
print("".join(KOREAN_CHARS))

# 폰트 로드 (비트맵 폰트 - size=16으로 렌더링, 실제 8x8 사용)
font = ImageFont.truetype(FONT_PATH, 16)

def render_char_8x8(ch):
    """문자를 8x8 픽셀 1비트 비트맵으로 렌더링"""
    img = Image.new('L', (16, 16), 255)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), ch, font=font, fill=0)
    # 좌상단 8x8만 추출
    pixels = list(img.getdata())
    bits = []
    for row in range(8):
        for col in range(8):
            pixel = pixels[row * 16 + col]
            bits.append(1 if pixel < 128 else 0)
    return bits  # 64 bits (8x8)

def bits_to_gb_tile(bits):
    """8x8 비트맵 → Game Boy 2BPP 타일 (16 bytes)"""
    tile = []
    for row in range(8):
        lo = 0
        hi = 0
        for col in range(8):
            bit = bits[row * 8 + col]
            # GB tile: col 0=MSB, col 7=LSB
            if bit:
                lo |= (1 << (7 - col))
                hi |= (1 << (7 - col))
        tile.append(lo)
        tile.append(hi)
    return bytes(tile)

def print_tile(bits, label=''):
    """타일을 ASCII 아트로 출력"""
    print(f"[{label}]")
    for row in range(8):
        line = ''
        for col in range(8):
            line += '█' if bits[row*8+col] else '·'
        print(f"  {line}")

# 한글 타일 추출
print("\n=== 타일 추출 중 ===")
tile_data = {}  # char -> GB tile bytes

# 샘플 미리보기
PREVIEW = ['가', '나', '한', '글', '경', '마', '도', '주']
for ch in PREVIEW:
    if ch in all_chars:
        bits = render_char_8x8(ch)
        print_tile(bits, ch)

# 전체 추출
for ch in KOREAN_CHARS:
    bits = render_char_8x8(ch)
    tile = bits_to_gb_tile(bits)
    tile_data[ch] = tile

print(f"\n{len(tile_data)}개 타일 추출 완료")

# --- ASCII 타일도 추출 (A-Z, 0-9, 특수문자) ---
# Game Boy에서 영문자는 이미 존재하므로 스킵

# --- 결과 저장 ---
# 1. 바이너리 타일 데이터 (모든 한글 타일 연속 저장)
tile_bin = b''
char_index = {}  # char -> index
for i, ch in enumerate(KOREAN_CHARS):
    tile_bin += tile_data[ch]
    char_index[ch] = i

tile_bin_path = OUT_DIR / 'korean_tiles.bin'
tile_bin_path.write_bytes(tile_bin)
print(f"타일 바이너리: {tile_bin_path} ({len(tile_bin)} bytes = {len(tile_bin)//16} tiles)")

# 2. 문자→인덱스 매핑 테이블
mapping_path = OUT_DIR / 'char_mapping.txt'
with open(mapping_path, 'w', encoding='utf-8') as f:
    f.write(f"# 한글 문자 → 타일 인덱스 매핑\n")
    f.write(f"# 총 {len(KOREAN_CHARS)}개 문자\n")
    f.write(f"# ROM 인코딩: 0x80(escape) + 인덱스 바이트\n\n")
    for i, ch in enumerate(KOREAN_CHARS):
        f.write(f"U+{ord(ch):04X} {ch} -> 인덱스 {i} (인코딩: 0x80 0x{i:02X})\n")

print(f"매핑 테이블: {mapping_path}")

# 3. 시각적 미리보기 이미지 생성
COLS = 16
ROWS = (len(KOREAN_CHARS) + COLS - 1) // COLS
preview_img = Image.new('RGB', (COLS * 10, ROWS * 10), (40, 40, 40))

for i, ch in enumerate(KOREAN_CHARS):
    bits = render_char_8x8(ch)
    row, col = divmod(i, COLS)
    for py in range(8):
        for px in range(8):
            x = col * 10 + px + 1
            y = row * 10 + py + 1
            if bits[py * 8 + px]:
                preview_img.putpixel((x, y), (200, 230, 200))
            else:
                preview_img.putpixel((x, y), (20, 20, 20))

preview_path = OUT_DIR / 'korean_tiles_preview.png'
preview_img.save(preview_path)
print(f"미리보기 이미지: {preview_path}")

# 4. GB 인코딩 테이블 요약
print(f"\n=== Game Boy 인코딩 방식 ===")
print(f"단일 바이트 (ASCII): 0x20-0x7F (기존 유지)")
print(f"한글 문자 (2바이트): 0x80 + [0x00-0x{len(KOREAN_CHARS)-1:02X}]")
print(f"  예: '가' = 0x80 0x{char_index['가']:02X}")
print(f"  예: '한' = 0x80 0x{char_index.get('한', 0):02X}")
print(f"  예: '글' = 0x80 0x{char_index.get('글', 0):02X}")
print(f"\n필요한 ROM 수정:")
print(f"  1. 텍스트 렌더러에 0x80 이스케이프 처리 추가")
print(f"  2. {len(tile_bin)//16}개 한글 타일 데이터를 ROM에 삽입")
print(f"  3. 기존 일본어 텍스트를 한국어로 교체")
