#!/usr/bin/env python3
"""
Winner's Horse Expanded ROM Patcher
입력: Winners_Horse_Expanded.gb (256KB, 뱅크 8에 한글 타일 배치됨)
출력: Winners_Horse_Korean.gb (완성된 한글화 ROM)

패치 내용:
  1. 뱅크 0 여유 공간 $0061~$00AA에 런타임 타일 로더 주입
  2. 후킹 포인트 2곳 (VRAM 클리어, $14D8 타일 로더)
  3. 텍스트 렌더러 카타카나 우회 패치
  4. 일본어 텍스트 → 한국어 인코딩
"""
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

ROM_IN  = '/home/user/gb_winners_horse/Winners_Horse_Expanded.gb'
ROM_OUT = '/home/user/gb_winners_horse/Winners_Horse_Korean.gb'

# ── 한국어 문자 집합 (extract_tiles.py / expand_rom.py 와 동일) ──────────────
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
KOREAN_BYTE_BASE = 0x21   # 한글 문자 i → ROM 바이트 값 0x21 + i

def encode_kr(text: str) -> bytes:
    result = []
    for ch in text:
        if '가' <= ch <= '힣':
            idx = CHAR_TO_IDX.get(ch)
            if idx is None:
                raise ValueError(f"문자 '{ch}'이 문자 집합에 없음")
            result.append(KOREAN_BYTE_BASE + idx)
    return bytes(result)

def center_pad(content: bytes, width: int, pad_byte: int = 0x20) -> bytes:
    content = content[:width]
    left  = (width - len(content)) // 2
    right = width - len(content) - left
    return bytes([pad_byte] * left) + content + bytes([pad_byte] * right)

# ── 텍스트 패치 테이블 ────────────────────────────────────────────────────────
PATCH_TABLE = [
    # 경주명 (22바이트 고정 슬롯: [03][20바이트 중앙정렬][00])
    (0x04F57, "사쓰키상",           'race22'),
    (0x04F6D, "천황상봄",           'race22'),
    (0x04F83, "야스다기념",         'race22'),
    (0x04F99, "일본더비",           'race22'),
    (0x04FAF, "다카라즈카기념",     'race22'),
    (0x04FC5, "천황상가을",         'race22'),
    (0x04FDB, "국화상",             'race22'),
    (0x04FF1, "마일챔피언십",       'race22'),
    (0x05007, "재팬컵",             'race22'),
    (0x0501D, "요코에컵",           'race22'),
    (0x05033, "아사히배세스테이크스",'race22'),
    (0x05049, "스프린터즈",         'race22'),
    (0x0505F, "아리마기념",         'race22'),
    (0x0B45A, "오카쇼",             'race22'),
    (0x0B49A, "오크스",             'race22'),
    (0x0B4EA, "엘리자베스여왕배",   'race22'),
    (0x1814B, "미승리전",           'race22'),
    (0x18159, "게이세이배",         'race22'),
    (0x18175, "게이머",             'race22'),
    (0x18199, "닛케이신춘배",       'race22'),
    (0x181AA, "신마전",             'race22'),
    (0x181B7, "다이아몬드",         'race22'),
    (0x181C7, "가쓰오",             'race22'),
    (0x181D2, "도쿄신문배",         'race22'),
    (0x181EF, "교토통신배",         'race22'),
    (0x18204, "기사라기상",         'race22'),
    (0x1822E, "메구로기념",         'race22'),
    (0x1823C, "교토기념",           'race22'),
    (0x18276, "호치배야요이상",     'race22'),
    (0x18287, "페가수스",           'race22'),
    (0x182A2, "나카야마기념",       'race22'),
    (0x182B0, "한신대상전",         'race22'),
    (0x182FB, "대상기념",           'race22'),
    (0x18325, "마이니치배",         'race22'),
    (0x1833C, "닛케이상",           'race22'),
    (0x1834A, "산케이오사카배",     'race22'),
    (0x18368, "크리스탈컵",         'race22'),
    (0x18422, "게이한배",           'race22'),
    (0x1846E, "한큐배",             'race22'),
    (0x18488, "엡솜컵",             'race22'),
    (0x18504, "다카마쓰노미야배",   'race22'),
    (0x18563, "삿포로세스테이크스", 'race22'),
    (0x185EA, "니가타세스테이크스", 'race22'),
    (0x185F9, "고쿠라세스테이크스", 'race22'),
    (0x18626, "센토르",             'race22'),
    (0x1868B, "고베신문배",         'race22'),
    (0x1869C, "하코다테세스테이크스",'race22'),
    (0x186AB, "마이니치왕관",       'race22'),
    (0x186BA, "교토대상전",         'race22'),
    (0x186DA, "교토신문배",         'race22'),
    (0x18715, "스완",               'race22'),
    (0x1873E, "네기시",             'race22'),
    (0x187A4, "마일챔피언십",       'race22'),
    (0x187D5, "요코에컵",           'race22'),
    (0x1880A, "스테이어즈",         'race22'),
    (0x18827, "나루오기념",         'race22'),
    (0x18856, "윈터",               'race22'),
    # 경마장 이름
    (0x0B65B, "한신",               'var'),
    (0x0B663, "주쿄",               'var'),
    (0x0B66B, "교토",               'var'),
    (0x0B673, "삿포로",             'var'),
    (0x0B67B, "하코다테",           'var'),
    (0x0B683, "후쿠시마",           'var'),
    (0x0B68B, "니가타",             'var'),
    (0x0B693, "고쿠라",             'var'),
    # UI/대화
    (0x040EE, "위와같이확정되었습니다", 'var'),
    (0x043DF, "기록이없습니다",         'var'),
    (0x05075, "성적전적승",             'var'),
    (0x05088, "상금",                   'var'),
    (0x05E26, "맑음",  'var'),
    (0x05E2A, "흐림",  'var'),
    (0x05E2F, "비",    'var'),
    (0x05E33, "폭풍",  'var'),
    (0x05E4F, "잔디",  'var'),
    # 말 정보 레이블 (뱅크 2)
    (0x0B55A, "두수는",               'var'),
    (0x0B5D1, "마장상태는",           'var'),
    (0x0B69B, "거리는얼마나됩니까",   'var'),
    (0x0B72E, "부담중량은",           'var'),
    (0x0B7A0, "두수",                 'var'),
    (0x0B7B5, "성별",                 'var'),
    (0x0B7C5, "부담중량",             'var'),
    (0x0B7D5, "기수실적",             'var'),
    (0x0B7E5, "코스",                 'var'),
    (0x0B7F5, "거리적성",             'var'),
    (0x0B805, "중마장적성",           'var'),
    (0x0B815, "등급",                 'var'),
    (0x0B825, "최근성적",             'var'),
    (0x0B835, "과거실적",             'var'),
    (0x0B845, "조교상태",             'var'),
    (0x0B855, "마체중",               'var'),
    (0x0B865, "휴양",                 'var'),
    (0x0B875, "마방",                 'var'),
    (0x0B885, "어느항목을수정하시겠습니까", 'var'),
    (0x0B972, "성별은",               'var'),
    # 주법
    (0x0BA41, "도주", 'var'),
    (0x0BA47, "선행", 'var'),
    (0x0BA4D, "차입", 'var'),
    (0x0BA53, "추입", 'var'),
    (0x0BA8D, "마장상태적성", 'var'),
    (0x0BAC6, "마체중증감",   'var'),
    (0x0BCAC, "핸디캡연승",   'var'),
    (0x18782, "미승리",       'var'),
    # 은퇴 메시지 (뱅크 7)
    (0x1E9AA, "은퇴까지년남았습니다",     'var'),
    (0x1E9BA, "은퇴까지년남았습니다",     'var'),
    (0x1E9CA, "은퇴까지년밖에않았습니다", 'var'),
]

def patch_string(rom: bytearray, offset: int, korean_text: str, slot_type: str):
    encoded = encode_kr(korean_text)
    if slot_type == 'race22':
        body = center_pad(encoded, 20, 0x20)
        new_bytes = bytes([0x03]) + body + bytes([0x00])
        assert len(new_bytes) == 22
        rom[offset:offset+22] = new_bytes
    elif slot_type == 'var':
        end = offset
        while end < offset + 64 and rom[end] != 0x00:
            end += 1
        orig_len = end - offset
        ctrl = rom[offset] if rom[offset] <= 0x03 else None
        if ctrl is not None:
            i = offset + 1
            spaces = []
            while i < end and rom[i] == 0x20:
                spaces.append(0x20); i += 1
            new_body = bytes([ctrl]) + bytes(spaces) + encoded
        else:
            new_body = encoded
        if len(new_body) < orig_len:
            new_body += bytes([0x20] * (orig_len - len(new_body)))
        elif len(new_body) > orig_len:
            new_body = new_body[:orig_len]
        rom[offset:offset+len(new_body)+1] = new_body + bytes([0x00])
    return encoded


def main():
    print("=== Winner's Horse Expanded ROM Patcher ===\n")

    with open(ROM_IN, 'rb') as f:
        rom = bytearray(f.read())
    assert len(rom) == 0x40000, f"입력 ROM 크기 오류: {len(rom)}"
    print(f"입력: {ROM_IN} ({len(rom)//1024}KB)")

    # ── 1. 뱅크 0 여유 공간에 런타임 타일 로더 주입 ──────────────────────────
    #
    # 메모리 맵 (뱅크 0, 항상 접근 가능):
    #   $0061-$0093 : korean_tile_loader  (51 bytes)
    #   $0094-$009C : fast_copy           ( 9 bytes)
    #   $009D-$00A3 : wrapper1            ( 7 bytes)  ← $14D8 내 $0491 대체
    #   $00A4-$00AA : wrapper2            ( 7 bytes)  ← VRAM 클리어 대체
    #
    # korean_tile_loader ($0061):
    #   LCD 꺼짐 확인 후, 뱅크 8 → VRAM 복사
    #   그룹1: CPU $4000-$45EF → VRAM $9210-$97FF (바이트 0x21-0x7F, 95타일)
    #   그룹2: CPU $45F0-$4ACF → VRAM $8800-$8CDF (바이트 0x80-0xCD, 78타일)
    #
    # 뱅크 8 타일 배치 (expand_rom.py 에서 이미 배치됨):
    #   file 0x20000 = CPU $4000 (뱅크 8) = 타일 0 (한글 '가', 바이트 0x21)
    #   file 0x205F0 = CPU $45F0           = 타일 95 (바이트 0x80)
    #
    # signed tile addressing (LCDC bit 4=0, 기준 $9000):
    #   타일 인덱스 +33 (0x21) → VRAM $9000 + 33×16 = $9210
    #   타일 인덱스 -128 (0x80) → VRAM $9000 - 128×16 = $8800

    loader_code = bytes([
        # $0061: korean_tile_loader
        0xF0, 0x40,          # LDH A,(FF40)      ; LCDC 레지스터 읽기
        0xCB, 0x7F,          # BIT 7,A            ; LCD 활성화 비트 확인
        0xC0,                # RET NZ             ; LCD ON이면 복귀 (VRAM 접근 불가)
        0xF5,                # PUSH AF
        0xC5,                # PUSH BC
        0xD5,                # PUSH DE
        0xE5,                # PUSH HL
        0xFA, 0xBE, 0xC0,    # LD A,($C0BE)       ; 현재 뱅크 번호 읽기
        0xF5,                # PUSH AF            ; 현재 뱅크 저장
        0x3E, 0x08,          # LD A,$08           ; 뱅크 8
        0xCD, 0x81, 0x04,    # CALL $0481         ; 뱅크 8로 전환
        # 그룹 1: 타일 0-94 → VRAM $9210-$97FF
        0x21, 0x00, 0x40,    # LD HL,$4000        ; 소스: 뱅크 8 시작 (타일 0)
        0x11, 0x10, 0x92,    # LD DE,$9210        ; 목적지: VRAM (바이트 0x21 → +33)
        0x01, 0xF0, 0x05,    # LD BC,$05F0        ; 95타일 × 16 = 1520 bytes
        0xCD, 0x94, 0x00,    # CALL $0094         ; fast_copy
        # 그룹 2: 타일 95-172 → VRAM $8800-$8CDF
        0x21, 0xF0, 0x45,    # LD HL,$45F0        ; 소스: 타일 95 (95×16=0x5F0)
        0x11, 0x00, 0x88,    # LD DE,$8800        ; 목적지: VRAM (바이트 0x80 → -128)
        0x01, 0xE0, 0x04,    # LD BC,$04E0        ; 78타일 × 16 = 1248 bytes
        0xCD, 0x94, 0x00,    # CALL $0094         ; fast_copy
        # 뱅크 복원
        0xF1,                # POP AF             ; A = 저장된 뱅크 번호
        0xCD, 0x81, 0x04,    # CALL $0481         ; 원래 뱅크로 복원
        0xE1,                # POP HL
        0xD1,                # POP DE
        0xC1,                # POP BC
        0xF1,                # POP AF
        0xC9,                # RET

        # $0094: fast_copy  (BC 바이트를 HL→DE로 복사, LCD 꺼짐 전제)
        0x2A,                # LD A,(HL+)
        0x12,                # LD (DE),A
        0x13,                # INC DE
        0x0B,                # DEC BC
        0x78,                # LD A,B
        0xB1,                # OR C
        0x20, 0xF8,          # JR NZ,-8           ; → $0094
        0xC9,                # RET

        # $009D: wrapper1  ($0491 원본 호출 후 한글 타일 로드)
        # file 0x1517 에서 CALL $0491 → CALL $009D 로 교체
        0xCD, 0x91, 0x04,    # CALL $0491
        0xCD, 0x61, 0x00,    # CALL $0061
        0xC9,                # RET

        # $00A4: wrapper2  ($05B7 VRAM 클리어 후 한글 타일 로드)
        # file 0x0233 에서 CALL $05B7 → CALL $00A4 로 교체
        0xCD, 0xB7, 0x05,    # CALL $05B7
        0xCD, 0x61, 0x00,    # CALL $0061
        0xC9,                # RET
    ])
    assert len(loader_code) == 74, f"로더 크기 오류: {len(loader_code)}"

    # 삽입 전: 해당 영역이 0x00으로 비어 있는지 확인
    for i, b in enumerate(rom[0x61:0x61+74]):
        assert b == 0x00, f"$0061+{i} 영역이 비어있지 않음: 0x{b:02X}"

    rom[0x0061:0x0061+74] = loader_code
    print(f"[1] 런타임 타일 로더 주입: file 0x0061-0x00AA ({len(loader_code)} bytes)")
    print(f"    $0061 korean_tile_loader (51b) | $0094 fast_copy (9b)")
    print(f"    $009D wrapper1 (7b) | $00A4 wrapper2 (7b)")

    # ── 2. 후킹 포인트 패치 ───────────────────────────────────────────────────
    # 2a. file 0x1517: CALL $0491 → CALL $009D  (inside $14D8, bank 4 active)
    assert bytes(rom[0x1517:0x151A]) == bytes([0xCD, 0x91, 0x04]), \
        f"0x1517 예상값 불일치: {bytes(rom[0x1517:0x151A]).hex()}"
    rom[0x1517] = 0xCD; rom[0x1518] = 0x9D; rom[0x1519] = 0x00
    print(f"[2a] 후킹: file 0x1517 CALL $0491 → CALL $009D  ($14D8 타일 로드 후 한글 타일)")

    # 2b. file 0x0233: CALL $05B7 → CALL $00A4  (VRAM 클리어 직후 한글 타일 재로드)
    assert bytes(rom[0x0233:0x0236]) == bytes([0xCD, 0xB7, 0x05]), \
        f"0x0233 예상값 불일치: {bytes(rom[0x0233:0x0236]).hex()}"
    rom[0x0233] = 0xCD; rom[0x0234] = 0xA4; rom[0x0235] = 0x00
    print(f"[2b] 후킹: file 0x0233 CALL $05B7 → CALL $00A4  (VRAM 클리어 후 재로드)")

    # ── 3. 텍스트 렌더러 패치 ($15C6) ────────────────────────────────────────
    # CP $A1 → JR +28 : 카타카나 분기 우회, 모든 바이트를 직접 타일 인덱스로 사용
    assert bytes(rom[0x15C6:0x15C8]) == bytes([0xFE, 0xA1]), \
        f"0x15C6 예상값 불일치: {bytes(rom[0x15C6:0x15C8]).hex()}"
    rom[0x15C6] = 0x18  # JR
    rom[0x15C7] = 0x1C  # +28 → $15E4
    print(f"[3]  텍스트 렌더러: file 0x15C6 FE A1 → 18 1C  (카타카나 처리 우회)")

    # ── 4. 텍스트 문자열 패치 ────────────────────────────────────────────────
    ok, err = 0, []
    seen = set()
    for offset, korean_text, slot_type in PATCH_TABLE:
        if offset in seen:
            continue
        seen.add(offset)
        try:
            patch_string(rom, offset, korean_text, slot_type)
            ok += 1
        except Exception as e:
            err.append((offset, korean_text, str(e)))
    print(f"[4]  텍스트 패치: {ok}개 성공, {len(err)}개 실패")
    for o, t, e in err:
        print(f"     ERR 0x{o:05X} '{t}': {e}")

    # ── 5. 출력 ─────────────────────────────────────────────────────────────
    with open(ROM_OUT, 'wb') as f:
        f.write(rom)
    print(f"\n[5]  출력: {ROM_OUT}")

    # ── 검증 ────────────────────────────────────────────────────────────────
    print("\n=== 검증 ===")
    print(f"  런타임 로더 $0061: {bytes(rom[0x61:0x65]).hex()}  (F040 CB7F = LDH A,LCDC; BIT 7,A)")
    print(f"  fast_copy  $0094: {bytes(rom[0x94:0x97]).hex()}  (2A 12 13 = LD A,(HL+); LD(DE),A; INC DE)")
    print(f"  wrapper1   $009D: {bytes(rom[0x9D:0xA0]).hex()}  (CD 9104 = CALL $0491)")
    print(f"  wrapper2   $00A4: {bytes(rom[0xA4:0xA7]).hex()}  (CD B705 = CALL $05B7)")
    print(f"  후킹 0x1517: {bytes(rom[0x1517:0x151A]).hex()}  (CD 9D00 = CALL $009D)")
    print(f"  후킹 0x0233: {bytes(rom[0x0233:0x0236]).hex()}  (CD A400 = CALL $00A4)")
    print(f"  텍스트렌더러: {bytes(rom[0x15C6:0x15C8]).hex()}  (18 1C = JR +28)")
    print(f"  뱅크8 타일[0]: {bytes(rom[0x20000:0x20008]).hex()}  (file 0x20000 = 한글 '가')")
    print(f"  뱅크4 원본 [0]: {bytes(rom[0x10000:0x10008]).hex()}  (원본 tile 0 그대로)")
    print(f"\n  한글 인코딩 예시:")
    for ch in ['가', '사', '한', '글']:
        if ch in CHAR_TO_IDX:
            b = KOREAN_BYTE_BASE + CHAR_TO_IDX[ch]
            vram = 0x9000 + (b if b < 0x80 else b - 0x100) * 16
            print(f"    '{ch}' → 바이트 0x{b:02X} → VRAM ${vram:04X}")


if __name__ == '__main__':
    main()
