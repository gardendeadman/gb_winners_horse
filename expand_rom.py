#!/usr/bin/env python3
"""
Winner's Horse ROM Expander
128KB → 256KB (뱅크 0-7 원본 보존, 뱅크 8-15 추가)
한글 타일 데이터를 뱅크 8 (file 0x20000)에 배치
"""
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

ROM_IN   = '/home/user/gb_winners_horse/Winners_Horse_Japan.gb'
ROM_OUT  = '/home/user/gb_winners_horse/Winners_Horse_Expanded.gb'
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
print(f"  카트리지 타입: 0x{orig[0x147]:02X} (MBC2+BATTERY)")
print(f"  ROM 크기 바이트: 0x{orig[0x148]:02X} → 128KB")

# 256KB로 확장 (뱅크 8-15 = 128KB 추가, 0xFF 패딩)
rom = orig + bytearray([0xFF] * 0x20000)
assert len(rom) == 0x40000  # 256KB
print(f"\n확장 후: {len(rom)//1024}KB (0xFF 패딩)")

# ── 뱅크 8에 한글 타일 배치 ────────────────────────────────────────────────
# 뱅크 8 = file 0x20000-0x23FFF (CPU $4000-$7FFF when bank 8 active)
# 타일 데이터: file 0x20000 (CPU $4000)
BANK8_START = 0x20000
TILES_CPU_BASE = 0x4000  # bank 8이 활성화됐을 때의 CPU 주소

with open(TILES_BIN, 'rb') as f:
    tile_data = f.read()

expected = NUM_TILES * 16
assert len(tile_data) == expected, f"타일 데이터 크기 불일치: {len(tile_data)} != {expected}"

rom[BANK8_START : BANK8_START + len(tile_data)] = tile_data
print(f"\n[뱅크 8] 한글 타일 {NUM_TILES}개 배치:")
print(f"  file 0x{BANK8_START:05X} ~ 0x{BANK8_START+len(tile_data)-1:05X}")
print(f"  CPU  0x{TILES_CPU_BASE:04X} ~ 0x{TILES_CPU_BASE+len(tile_data)-1:04X} (뱅크 8 활성 시)")
print(f"  크기: {len(tile_data)} bytes ({NUM_TILES} tiles × 16 bytes)")

# 타일 그룹별 VRAM 목적지 (signed tile addressing, 기준주소 $9000)
# 그룹 1: 바이트 0x21-0x7F (signed +33~+127) → VRAM $9210~$97F0
# 그룹 2: 바이트 0x80-0xCD (signed -128~-51)  → VRAM $8800~$8CD0
group1_count = 0x7F - 0x21 + 1   # 95 tiles
group2_count = 0xCD - 0x80 + 1   # 78 tiles
assert group1_count + group2_count == NUM_TILES, \
    f"{group1_count}+{group2_count}={group1_count+group2_count} != {NUM_TILES}"

group1_vram_start = 0x9000 + 0x21 * 16  # $9210
group2_vram_start = 0x9000 + (0x80 - 0x100) * 16  # $8800 (0x80 as signed -128)

print(f"\n  그룹 1 (바이트 0x21-0x7F, {group1_count}타일):")
print(f"    ROM:  file 0x{BANK8_START:05X} ~ 0x{BANK8_START + group1_count*16 - 1:05X}")
print(f"    VRAM: ${group1_vram_start:04X} ~ ${group1_vram_start + group1_count*16 - 1:04X}")
print(f"  그룹 2 (바이트 0x80-0xCD, {group2_count}타일):")
print(f"    ROM:  file 0x{BANK8_START + group1_count*16:05X} ~ 0x{BANK8_START + NUM_TILES*16 - 1:05X}")
print(f"    VRAM: ${group2_vram_start:04X} ~ ${group2_vram_start + group2_count*16 - 1:04X}")

# ── 헤더 업데이트 ────────────────────────────────────────────────────────────
# ROM 크기 바이트 0x0148: 0x02 (128KB) → 0x03 (256KB)
rom[0x0148] = 0x03
print(f"\n[헤더] ROM 크기 바이트 0x0148: 0x02 → 0x03 (256KB)")

# 헤더 체크섬 재계산 (0x014D)
# 범위: 0x0134-0x014C (제목, MBC, ROM크기 등)
checksum = 0
for i in range(0x0134, 0x014D):
    checksum = (checksum - rom[i] - 1) & 0xFF
rom[0x014D] = checksum
print(f"[헤더] 체크섬 0x014D 재계산: 0x{checksum:02X}")

# 글로벌 체크섬 재계산 (0x014E-0x014F)
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

print(f"\n✓ 출력: {ROM_OUT}")
print(f"  크기: {len(rom)//1024}KB")
print(f"  뱅크 0-7: 원본 그대로 (변경 없음)")
print(f"  뱅크 8:   한글 타일 {NUM_TILES}개 + 0xFF 패딩")
print(f"  뱅크 9-15: 0xFF 패딩 (미사용)")
print(f"\n※ 다음 단계: 뱅크 8에서 VRAM으로 런타임 로딩 코드 주입")
print(f"   - 뱅크 전환: LD A,$08; CALL $0481")
print(f"   - 타일 복사: $4000→VRAM $9210 (그룹1), $45F0→VRAM $8800 (그룹2)")

# 검증
print(f"\n=== 검증 ===")
print(f"원본 뱅크 4 타일 데이터 (file 0x10090): {bytes(rom[0x10090:0x10098]).hex()}")
print(f"뱅크 8 한글 타일 첫 8바이트 (file 0x20000): {bytes(rom[0x20000:0x20008]).hex()}")
print(f"원본 뱅크 4 유지 확인: {bytes(rom[0x10090:0x10098]).hex() == bytes(orig[0x10090:0x10098]).hex()}")
