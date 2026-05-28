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
  2. 한글 byte B (0x21-0xCD) 슬롯을 한글 글리프로 교체:
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

# 단계 1: 뱅크 4 타일 영역 → 뱅크 8에 복사 (space, 숫자 등 비한글 문자 유지)
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

# 단계 3: 한글 타일을 뱅크 8의 해당 슬롯에 배치
KOREAN_BYTE_BASE = 0x21  # '가'(idx 0) = byte 0x21
placed = 0
for i, ch in enumerate(KOREAN_CHARS):
    byte_val = KOREAN_BYTE_BASE + i   # 0x21 ~ 0xCD
    tile_16  = tile_data_16[i*16 : i*16+16]
    tile_8   = tile_16_to_8(tile_16)

    # 뱅크 8 파일 오프셋: 0x20000 + ($4090 + byte_val*8 - $4000)
    file_offset = BANK8_TILE_START + byte_val * 8   # = 0x20090 + byte_val*8
    rom[file_offset : file_offset + 8] = tile_8
    placed += 1

print(f"\n[뱅크 8] 한글 타일 {placed}개 배치 (8byte/tile 포맷):")
print(f"  바이트 0x{KOREAN_BYTE_BASE:02X}-0x{KOREAN_BYTE_BASE+NUM_TILES-1:02X}"
      f" → file 0x{BANK8_TILE_START + KOREAN_BYTE_BASE*8:05X}"
      f"-0x{BANK8_TILE_START + (KOREAN_BYTE_BASE+NUM_TILES-1)*8 + 7:05X}")
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
print(f"bank4 타일 영역 보존: {bytes(rom[0x10090:0x10098]).hex()}")
print(f"bank8 space(0x20) 타일 (file 0x{0x20090+0x20*8:05X}): "
      f"{bytes(rom[0x20090+0x20*8 : 0x20090+0x20*8+8]).hex()}")
print(f"bank4 space(0x20) 타일 (file 0x{0x10090+0x20*8:05X}): "
      f"{bytes(rom[0x10090+0x20*8 : 0x10090+0x20*8+8]).hex()}")
kr0_off = BANK8_TILE_START + KOREAN_BYTE_BASE * 8
print(f"bank8 한글[0](가, 0x21) 타일 (file 0x{kr0_off:05X}): "
      f"{bytes(rom[kr0_off:kr0_off+8]).hex()}")
print(f"bank4 원본 0x21 슬롯 (file 0x{0x10090+0x21*8:05X}): "
      f"{bytes(rom[0x10090+0x21*8 : 0x10090+0x21*8+8]).hex()}")
print(f"bank4 원본 불변 확인: {bytes(rom[0x10090:0x10098]) == bytes(orig[0x10090:0x10098])}")
