#!/usr/bin/env python3
"""
Winner's Horse ROM Expander
128KB → 256KB (뱅크 0-7 원본 보존, 뱅크 8 한글 타일 배치)

게임 텍스트 렌더러 온디맨드 로더 분석 결과:
  - 로더 공식: CPU $4090 + char_byte × 8  (bank4 활성 시)
  - 타일 형식: 8 bytes/tile (1 byte/row, lo plane = hi plane)
  - $04B6이 PUSH AF / POP AF로 A 보존 → 두 번째 쓰기도 동일 바이트

뱅크 8 구성:
  1. bank4 타일 영역($10090-$10890) 복사 → bank8($20090-$20890)
     (space, 숫자 등 비한글 문자 유지)
  2. 한글 byte B (0x21-0xDD) 슬롯을 한글 글리프로 교체:
     file 0x20090 + B*8 = 한글 타일 i (8byte 변환)
"""
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

ROM_IN    = '/home/user/gb_winners_horse/Winners_Horse_Japan.gb'
ROM_OUT   = '/home/user/gb_winners_horse/Winners_Horse_Expanded.gb'
TILES_BIN = '/home/user/gb_winners_horse/tiles/korean_tiles.bin'

# Korean charset (must match extract_tiles.py order)
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
    # 코스 설명 (새 문자)
    "평탄해직긴파워반너좌회내모안쪽유",
    # 추가 번역 (14 신규 문자)
    "레이스의이번주일후늘출할합있능력뉴돌처단",
    # 트레이너 이름 + 대화 (4 신규 문자)
    "바무켄임",
]

all_chars = set()
for text in TRANSLATIONS_SRC:
    for ch in text:
        if '가' <= ch <= '힣':
            all_chars.add(ch)
KOREAN_CHARS = sorted(all_chars)
NUM_TILES = len(KOREAN_CHARS)

print("=== Winner's Horse ROM Expander ===")

# 원본 ROM 로드
with open(ROM_IN, 'rb') as f:
    orig = bytearray(f.read())

assert len(orig) == 0x20000, f"예상 크기 128KB != {len(orig)}"
print(f"원본 ROM: {len(orig)//1024}KB")

# 256KB로 확장 (뱅크 8-15 = 128KB 추가, 0xFF 패딩)
rom = orig + bytearray([0xFF] * 0x20000)
assert len(rom) == 0x40000
print(f"확장 후: {len(rom)//1024}KB")

# ── 뱅크 8 구성 ────────────────────────────────────────────────────────────────
# 온디맨드 로더 공식: HL = $4090 + char_byte × 8 (in active bank)
# → 뱅크 8의 타일 테이블이 뱅크 4와 동일한 레이아웃이어야 함
# → bank4 타일 영역 복사 후 한글 슬롯만 교체

BANK4_TILE_START = 0x10090   # file: bank4 CPU $4090
BANK8_TILE_START = 0x20090   # file: bank8 CPU $4090 (bank8 = file 0x20000)
TILE_AREA_SIZE   = 256 * 8   # 모든 byte 값(0-255) 커버, 8 bytes/tile = 2048 bytes

# 단계 1: 뱅크 4 타일 영역 → 뱅크 8에 복사 (모든 원본 타일 보존)
rom[BANK8_TILE_START : BANK8_TILE_START + TILE_AREA_SIZE] = \
    rom[BANK4_TILE_START : BANK4_TILE_START + TILE_AREA_SIZE]
print(f"\n[뱅크 8] bank4 타일 영역 복사:")
print(f"  file 0x{BANK4_TILE_START:05X}-0x{BANK4_TILE_START+TILE_AREA_SIZE-1:05X}"
      f" → file 0x{BANK8_TILE_START:05X}-0x{BANK8_TILE_START+TILE_AREA_SIZE-1:05X}"
      f" ({TILE_AREA_SIZE} bytes)")

# 단계 2: 16-byte GB 2BPP 타일 → 8-byte 게임 포맷으로 변환
# 게임 로더: 같은 1-byte 소스로 lo-plane과 hi-plane 모두 씀
# 변환: 각 row에서 source_byte = lo_plane | hi_plane (두 플레인 OR)
with open(TILES_BIN, 'rb') as f:
    tile_data_16 = f.read()

assert len(tile_data_16) == NUM_TILES * 16, \
    f"타일 데이터 크기 불일치: {len(tile_data_16)} != {NUM_TILES*16}"

def tile_16_to_8(tile_16: bytes) -> bytes:
    """16-byte GB 2BPP tile → 8-byte single-plane (lo|hi per row)"""
    result = []
    for row in range(8):
        lo = tile_16[row * 2]
        hi = tile_16[row * 2 + 1]
        result.append(lo | hi)
    return bytes(result)

# 보존 바이트: 게임이 실제로 사용하는 타일 (숫자, 공백, 구두점)
# 이 위치에는 한글 타일을 덮어쓰지 않고 bank4 원본 유지
PRESERVED = set(list(range(0x30, 0x3A)) + [0x20, 0x2C, 0x3C, 0x3F])

# 한글 타일 배치 가능한 바이트 슬롯 (오름차순, $21부터 $FF까지, 보존 제외)
available_positions = [b for b in range(0x21, 0x100) if b not in PRESERVED]
assert len(available_positions) >= NUM_TILES, \
    f"사용 가능 슬롯 {len(available_positions)} < 필요 타일 {NUM_TILES}"

# 단계 3: 한글 타일을 뱅크 8의 해당 슬롯에 배치 (보존 위치 건너뜀)
placed = 0
for i, ch in enumerate(KOREAN_CHARS):
    byte_val = available_positions[i]
    tile_16  = tile_data_16[i*16 : i*16+16]
    tile_8   = tile_16_to_8(tile_16)
    file_offset = BANK8_TILE_START + byte_val * 8
    rom[file_offset : file_offset + 8] = tile_8
    placed += 1

first_byte = available_positions[0]
last_byte  = available_positions[NUM_TILES - 1]
print(f"\n[뱅크 8] 한글 타일 {placed}개 배치 (8byte/tile 포맷):")
print(f"  바이트 범위: 0x{first_byte:02X}~0x{last_byte:02X} "
      f"(보존 슬롯 {sorted(PRESERVED)} 건너뜀)")
print(f"  $30-$39 숫자 타일 보존 확인 (bank4→bank8 유지)")
print(f"  공식: file 0x20090 + byte_val×8 (= bank8 CPU $4090 + byte_val×8)")

# ── 헤더 업데이트 ────────────────────────────────────────────────────────────
rom[0x0148] = 0x03
print(f"\n[헤더] ROM 크기 0x0148: 0x02 → 0x03 (256KB)")

checksum = 0
for i in range(0x0134, 0x014D):
    checksum = (checksum - rom[i] - 1) & 0xFF
rom[0x014D] = checksum
print(f"[헤더] 체크섬 0x014D: 0x{checksum:02X}")

global_sum = 0
for i in range(len(rom)):
    if i not in (0x014E, 0x014F):
        global_sum = (global_sum + rom[i]) & 0xFFFF
rom[0x014E] = (global_sum >> 8) & 0xFF
rom[0x014F] = global_sum & 0xFF
print(f"[헤더] 글로벌 체크섬: 0x{global_sum:04X}")

# ── 출력 ─────────────────────────────────────────────────────────────────────
with open(ROM_OUT, 'wb') as f:
    f.write(rom)
print(f"\n✓ 출력: {ROM_OUT} ({len(rom)//1024}KB)")

# 검증
print("\n=== 검증 ===")
print(f"bank4 타일 영역 불변: {bytes(rom[0x10090:0x10098]).hex()}")
# 숫자 타일 보존 확인
for digit in range(10):
    b = 0x30 + digit
    b4 = bytes(rom[0x10090+b*8 : 0x10090+b*8+8]).hex()
    b8 = bytes(rom[0x20090+b*8 : 0x20090+b*8+8]).hex()
    match = "OK" if b4 == b8 else "MISMATCH!"
    print(f"  숫자 '{digit}' (0x{b:02X}): bank4={b4}  bank8={b8}  [{match}]")
# 한글 첫 번째 타일 확인
b0 = available_positions[0]
kr0_off = BANK8_TILE_START + b0 * 8
print(f"bank8 한글[0]('{KOREAN_CHARS[0]}', 0x{b0:02X}) 타일: "
      f"{bytes(rom[kr0_off:kr0_off+8]).hex()}")
