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
    # 코스 설명 (새 문자)
    "평탄해직긴파워반너좌회내모안쪽유",
    # 추가 번역 (14 신규 문자)
    "레이스의이번주일후늘출할합있능력뉴돌처단",
    # 트레이너 이름 + 대화 (4 신규 문자)
    "바무켄임",
    # 메뉴 (1 신규 문자: 틀)
    "타이틀로",
]

all_chars = set()
for text in TRANSLATIONS_SRC:
    for ch in text:
        if '가' <= ch <= '힣':
            all_chars.add(ch)
KOREAN_CHARS = sorted(all_chars)

# 보존 바이트: expand_rom.py 와 동일 (숫자·공백·구두점 타일 유지)
PRESERVED = set(list(range(0x30, 0x3A)) + [0x20, 0x2C, 0x3C, 0x3F])
available_positions = [b for b in range(0x21, 0x100) if b not in PRESERVED]
CHAR_TO_BYTE = {ch: available_positions[i] for i, ch in enumerate(KOREAN_CHARS)}

def encode_kr(text) -> bytes:
    if isinstance(text, (bytes, bytearray)):
        return bytes(text)
    result = []
    for ch in text:
        if '가' <= ch <= '힣':
            b = CHAR_TO_BYTE.get(ch)
            if b is None:
                raise ValueError(f"문자 '{ch}'이 문자 집합에 없음")
            result.append(b)
        elif ch == ' ':  result.append(0x20)
        elif ch == '\n': result.append(0x02)
        elif '\x01' <= ch <= '\x0f': result.append(ord(ch))  # control/runtime codes
        elif '0' <= ch <= '9': result.append(ord(ch))
    return bytes(result)

def center_pad(content: bytes, width: int, pad_byte: int = 0x20) -> bytes:
    content = content[:width]
    left  = (width - len(content)) // 2
    right = width - len(content) - left
    return bytes([pad_byte] * left) + content + bytes([pad_byte] * right)

def _build_data_select():
    """0x0436D: 저장 선택 박스 (박스 그리기 타일 $60-$67 보존)"""
    ek = encode_kr
    row = lambda c: bytes([0x63]) + c + bytes([0x64, 0x01])
    def slot(label_bytes, digit):
        return bytes([0x20, 0x20]) + label_bytes + bytes([digit, 0x20, 0x20, 0x20])
    lbl = ek("기록")  # 기,록 → 기록N = save slot label
    return (bytes([0x03, 0x60]) + bytes([0x61]*7) + bytes([0x62, 0x01]) +
            row(slot(lbl, 0x31)) + row(slot(lbl, 0x32)) +
            row(slot(lbl, 0x33)) + row(slot(lbl, 0x34)) +
            row(bytes([0x20, 0x20]) + ek("없음") + bytes([0x20]*4)) +
            bytes([0x65]) + bytes([0x66]*8) + bytes([0x67]))
DATA_SELECT_PATCH = _build_data_select()

def _build_load_box():
    """0x0429B: 불러오기 선택 박스 (147B): 03 60 61×18 62 + 5×row + footer"""
    ek = encode_kr
    top    = bytes([0x03, 0x60]) + bytes([0x61]*18) + bytes([0x62])
    footer = bytes([0x01, 0x65]) + bytes([0x66]*18) + bytes([0x67])
    def row(content):
        return bytes([0x01, 0x63]) + content + bytes([0x64])
    def data_slot(n):
        return row(bytes([0x20]*3) + ek("기록") + bytes([0x30+n]) + bytes([0x20]*12))
    cancel = row(bytes([0x20]*5) + ek("없음") + bytes([0x20]*11))
    return top + data_slot(1) + data_slot(2) + data_slot(3) + data_slot(4) + cancel + footer
LOAD_BOX_PATCH = _build_load_box()

def _build_question_box():
    """0x04341: 어느기록입니까? 질문 박스 (43B)"""
    ek = encode_kr
    text    = ek("어느기록입니까") + bytes([0x3F])  # 8B
    content = bytes([0x20]*6) + text + bytes([0x20]*6)  # 20B
    return (bytes([0x01, 0x03, 0x63]) + content +
            bytes([0x64, 0x01, 0x65]) + bytes([0x66]*16) + bytes([0x67]))
QUESTION_BOX_PATCH = _build_question_box()

def _build_prize_block(preamble: bytes, size: int) -> bytes:
    """레이스 결과 + 상금 표시 블록 (preamble + 상금행 + 전체상금행)"""
    ek = encode_kr
    prize1 = bytes([0x01, 0x03]) + ek("상금") + bytes([0x20]*6) + bytes([0x30, 0x68, 0x6C])
    prize2 = bytes([0x01]) + ek("전체상금") + bytes([0x20]*2) + bytes([0x30, 0x68, 0x6C])
    return preamble + prize1 + prize2

ek = encode_kr
_PRIZE_BASE_1 = _build_prize_block(
    bytes([0x02, 0x20, 0x20, 0x20]) + ek("레이스") + bytes([0x03]) + ek("승리") + bytes([0x01, 0x01]), 45)
_PRIZE_BASE_SPEED = _build_prize_block(
    bytes([0x02]) + ek("스피드") + bytes([0x03]) + ek("대시능력") +
    bytes([0x01]) + ek("있습니다") + bytes([0x01, 0x01]), 60)
_PRIZE_BASE_STAMINA = _build_prize_block(
    bytes([0x02]) + ek("스태미나") + bytes([0x03]) + ek("파워능력") +
    bytes([0x01]) + ek("있습니다") + bytes([0x01, 0x01]), 57)

def _build_stamina_max(leading_spaces: int) -> bytes:
    ek = encode_kr
    return (bytes([0x02]) + bytes([0x20]*leading_spaces) +
            ek("스태미나") + bytes([0x03]) +
            ek("최대입니다") + bytes([0x01, 0x02, 0x6E, 0x6F]))
_STAMINA_MAX_1 = _build_stamina_max(4)   # 0x068D9 (25B slot)
_STAMINA_MAX_2 = _build_stamina_max(2)   # 0x068F3 (24B slot)

def _build_trainer_prize():
    """0x0514A (29B): \x01 200000 [0x68][0x6C] \x03 대단합니다 \x01"""
    return (bytes([0x01, 0x32, 0x30, 0x30, 0x30, 0x30, 0x30, 0x68, 0x6C, 0x03]) +
            encode_kr("대단합니다") + bytes([0x01]))
_TRAINER_PRIZE = _build_trainer_prize()

def _build_weekly_stats():
    """0x06970 (97B): 주간 성적 통계 블록"""
    ek = encode_kr
    r = bytearray()
    # [0-12] 스태미나 라벨 + 게이지 바
    r += bytes([0x01, 0x02]) + ek("스태미나") + bytes([0x20]*5) + bytes([0x08, 0x09])
    # [13-28] 섹션 헤더 ($ = 런타임 값 마커)
    r += bytes([0x01, 0x01, 0x03, 0x20, 0x20, 0x20, 0x20, 0x24])
    r += ek("이번주성적") + bytes([0x20]*3)
    # [29-41] Gy 행
    r += bytes([0x01, 0x47, 0x79]) + bytes([0x20]*7) + ek("승") + bytes([0x20]*2)
    # [42-54] Gz 행
    r += bytes([0x01, 0x47, 0x7A]) + bytes([0x20]*7) + ek("승") + bytes([0x20]*2)
    # [55-67] G{ 행
    r += bytes([0x01, 0x47, 0x7B]) + bytes([0x20]*7) + ek("승") + bytes([0x20]*2)
    # [68-82] 전체 섹션
    r += bytes([0x01, 0x02]) + ek("전체") + bytes([0x20]*7) + bytes([0x03]) + ek("레이스")
    # [83-96] 레이스 섹션
    r += bytes([0x01]) + ek("레이스") + bytes([0x02]) + ek("레이스") + bytes([0x20]*3) + ek("레이스")
    assert len(r) == 97, f"weekly stats size = {len(r)}"
    return bytes(r)
_WEEKLY_STATS = _build_weekly_stats()

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
    # 레이스 스케줄 (뱅크 1)
    (0x05724, "\x03의\n레이스",              'multiline'),
    (0x0572B, "\x03이번주의\n레이스",         'multiline'),
    (0x05737, "\x031주일후의\n레이스",        'multiline'),
    (0x05746, "\x032주일후의\n레이스",        'multiline'),
    (0x05755, "\x033주일후의\n레이스",        'multiline'),
    (0x05768, "\x03은더이상없습니다",         'multiline'),
    # 트라이얼 경주명 (뱅크 1)
    (0x0579B, "\x03사쓰키상\n 트라이얼",     'multiline'),
    (0x057AA, "\x03천황상\n 트라이얼",       'multiline'),
    (0x057C8, "\x03야스다기념\n 트라이얼",   'multiline'),
    (0x057D8, "\x03국화상\n 트라이얼",       'multiline'),
    # 능력 파라미터 (뱅크 1) ─ 스태미나/스피드/파워/대시 레이블
    (0x06151, "\x03에는\x01\x03    자신감 있습니다\x01\x01\x01"
              "\x03        능력\n파라미터\x01"
              "\n스태미나   8 스피드 20\x01"
              "\n파워   6 대시   6",          'multiline'),
    (0x061DA, "\x03가 있어\x01"
              "\x03        능력\n파라미터\x01"
              "\n스태미나   8 스피드  6\x01"
              "\n파워  20 대시   6",          'multiline'),
    (0x06280, "\x03        능력\n파라미터\x01"
              "\n스태미나  10 스피드 10\x01"
              "\n파워  10 대시  10",          'multiline'),
    (0x06303, "\x03        능력\n파라미터\x01"
              "\n스태미나  20 스피드  8\x01"
              "\n파워   6 대시   6",          'multiline'),
    (0x0635F, "\x03        능력\n파라미터\x01"
              "\n스태미나   8 스피드  6\x01"
              "\n파워   6 대시  20",          'multiline'),
    (0x0640A, "\x03        능력\n파라미터\x01"
              "\n스태미나  20 스피드  6\x01"
              "\n파워   8 대시   8",          'multiline'),
    # 출전/퇴장 메시지 (뱅크 1)
    (0x06657, "\x03오늘출전할수있는\n레이스\x03없습니다", 'multiline'),
    (0x06675, "\x03더이상\n연습은\x03할수없습니다",        'multiline'),
    (0x0668C, "\x03이\n레이스\x03에는\x01출전할수없습니다",'multiline'),
    (0x066E1, "\x03에출전합니까?",            'multiline'),
    (0x06708, "\x034주가됩니다",              'multiline'),
    # 메뉴 (뱅크 1)
    (0x069E3, "\x03처음부터\x01\x03이어하기", 'multiline'),
    (0x06A30, "\x03돌아가기\x01\x03없음",     'multiline'),
    (0x06AB8, "\x03이전\n메뉴\x03로돌아가기", 'multiline'),
    # 뱅크 6 경주 타입
    (0x183C5, "\x03신마전",                   'multiline'),
    (0x184BF, "\x03미승리전",                 'multiline'),
    (0x184D2, "\x03단파상",                   'multiline'),
    (0x1859C, "\x03미승리전",                 'multiline'),
    # 트레이너 이름 (뱅크 1)
    (0x0661A, "\x03다카노 히로시",  'multiline'),
    (0x06623, "\x03바바 다다시",    'multiline'),
    (0x0662E, "\x03기무라 요시오",  'multiline'),
    (0x06637, "\x03야마무라 켄지",  'multiline'),
    (0x06642, "\x03미즈노 사부로",  'multiline'),
    (0x0664E, "\x03가쓰 야마모토", 'multiline'),
    # 트레이너 대화 (뱅크 1)
    (0x050E8, "\x03나의 연습\x01\x03성과가\n있습니다",         'multiline'),
    (0x05168, "\x03나의 연습이\x01\x03어느정도\n됩니까",       'multiline'),
    (0x051E5, "\x03이 게임\n마무리에\x03는",                   'multiline'),
    (0x0525B, "\x03이 게임\n마무리에\x03는",                   'multiline'),
    # 코스 설명 (뱅크 1 0x05E6F-0x060C9)
    (0x05E6F, "이 삿포로 코스는 평탄해",                   'var'),
    (0x05E91, "이 하코다테 코스는 평탄해",                 'var'),
    (0x05EB3, "이 후쿠시마 코스는 평탄해",                 'var'),
    (0x05ED4, "이 니가타 코스는 직선이 긴 코스야",         'var'),
    (0x05F0F, "이 도쿄 코스는 스태미나 파워가 중요해",     'var'),
    (0x05F49, "이 나카야마 코스는 스태미나 파워가 중요해", 'var'),
    (0x05F86, "이 주쿄 코스는 후반 코너가 중요해 좌회전 코스야",   'var'),
    (0x05FC9, "이 교토 코스는 후반 내리기가 중요해",       'var'),
    (0x05FFD, "이 한신 코스는 평탄해도 모양이 특이해",     'var'),
    (0x06045, "이 고쿠라 코스는 평탄해 안쪽이 유리해",     'var'),
    (0x06089, "잔디 코스는 평탄해",                        'var'),
    (0x060A9, "잔디 코스는 평탄해",                        'var'),
    (0x060C9, "이 특별 코스는 장거리야 스태미나 중요해",   'var'),
    # 데이터 선택 박스 (뱅크 1)
    (0x0436D, DATA_SELECT_PATCH, 'multiline'),
    # 레이스/관전 서브메뉴 (뱅크 1)
    (0x069D2, "\x02레이스하기\x01\x03관전하기",  'multiline'),
    # 주간 메인 메뉴 7항목 (뱅크 1)
    (0x069F3, "\x02레이스하기\x01\x02연습하기\x01\x03휴양하기\x01\x03마기록\x01\x02레이스일정\x01\x02타이틀로\x01\x03없음", 'multiline'),
    # 트레이닝 선택 + 스탯 표시 (뱅크 1)
    (0x06A40, "\x03자기연습\x01\x02 트레이너대행\x01\x01\x01\x02스태미나  \x08\x09\x01스피드    \x08\x09\x01파워      \x08\x09\x01대시      \x08\x09", 'multiline'),
    # 능력치 항목 선택 (뱅크 1)
    (0x06A88, "\x03어느항목을연습합니까\x01\x01 1  스태미나\x01 2  스피드\x01 3  파워\x01 4  대시", 'multiline'),
    # 달력 주차 표시 (뱅크 1)
    (0x06AC8, "\x03\x0b 주차", 'multiline'),
    # 불러오기 선택 박스 (뱅크 1)
    (0x0429B, LOAD_BOX_PATCH, 'multiline'),
    # 어느 기록입니까? 질문 박스 (뱅크 1)
    (0x04341, QUESTION_BOX_PATCH, 'multiline'),
    # 레이스/트레이너 선택 프롬프트 (뱅크 1)
    (0x066A6, "\x02\x03어느레이스입니까",       'multiline'),
    (0x066B4, "\x03이능력치는\x01더이상오르지않습니다", 'multiline'),
    (0x066CB, "\x02\x03어느트레이너입니까",      'multiline'),
    (0x066F0, "\x02\x03어느레이스입니까",        'multiline'),
    (0x06700, "\x02연습은\x034주가됩니다",       'multiline'),
    (0x06715, "\x03이트레이너로는\x01안됩니다",  'multiline'),
    # 레이스 결과 + 상금 표시 (뱅크 1)
    (0x06752, _PRIZE_BASE_1,      'multiline'),
    (0x067B0, _PRIZE_BASE_SPEED,  'multiline'),
    (0x067ED, _PRIZE_BASE_STAMINA,'multiline'),
    # 스태미나 최대 메시지 (뱅크 1)
    (0x068D9, _STAMINA_MAX_1, 'multiline'),
    (0x068F3, _STAMINA_MAX_2, 'multiline'),
    # 트레이너 대화 (뱅크 1)
    (0x050B4, "\x03긴레이스에는\x02스태미나가\x01중요합니다", 'multiline'),
    (0x05112, "\x03대단합니다\x01여기까지\x01오다니",         'multiline'),
    (0x0514A, _TRAINER_PRIZE, 'multiline'),
    (0x05195, "\x03나는어느쪽입니까",                        'multiline'),
    (0x052FB, "\x03대단합니다",                              'multiline'),
    # 레이스 스타트 안내 (뱅크 1)
    (0x0587B, "\x03스타트합니다\x01\x01이코스는\x03스태미나\x01주의하세요\x01\x01\x03레이스스타트", 'multiline'),
    # 주간 성적 통계 (뱅크 1)
    (0x06970, _WEEKLY_STATS, 'multiline'),
]

def patch_string(rom: bytearray, offset: int, korean_text, slot_type: str):
    encoded = encode_kr(korean_text)
    if slot_type == 'multiline':
        # 원본 길이 파악 후 인코딩 결과를 그대로 기록 (공백 패딩/잘라내기)
        end = offset
        while end < offset + 300 and rom[end] != 0x00:
            end += 1
        orig_len = end - offset
        data = encoded
        if len(data) < orig_len:
            data += bytes([0x20] * (orig_len - len(data)))
        else:
            data = data[:orig_len]
        rom[offset:offset + orig_len + 1] = data + bytes([0x00])
        return data
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

    # ── 1. 온디맨드 타일 로더 bank4 → bank8 전환 ─────────────────────────────
    # 텍스트 렌더러 on-demand loader ($160A~):
    #   LD A, $04      ; ← bank4 (file 0x160A = 0x04)
    #   CALL $0481     ; bank 전환
    #   LD HL, $4090   ; 타일 테이블 베이스
    #   LD DE, $0008   ; 곱수 8 (8 bytes/tile)
    #   LD A, C        ; char byte
    #   RST $18        ; HL = $4090 + char×8 (in active bank)
    #
    # 뱅크 8 구조 (expand_rom.py 참조):
    #   bank4 타일 영역 복사 + 한글 슬롯 교체
    #   → bank4 → bank8로 바꾸기만 하면 됨 (베이스 주소 유지)
    assert rom[0x160A] == 0x04, f"file 0x160A 예상 0x04, 실제 0x{rom[0x160A]:02X}"
    rom[0x160A] = 0x08
    print(f"[1] 온디맨드 로더 bank 전환: file 0x160A  04 → 08  (bank4 → bank8)")

    # ── 2. 텍스트 렌더러 패치 ($15C6) ────────────────────────────────────────
    # CP $A1 → JR +28: 바이트 $A1-$DF 가타카나 변환 경로 우회
    # → 한글 바이트 $A1-$CD가 올바른 온디맨드 로더 경로($15E4)로 진입
    # (바이트 $21-$A0은 원래부터 $15E4로 진입, 이 패치로 $A1-$CD도 동일하게 처리)
    assert bytes(rom[0x15C6:0x15C8]) == bytes([0xFE, 0xA1]), \
        f"0x15C6 예상값 불일치: {bytes(rom[0x15C6:0x15C8]).hex()}"
    rom[0x15C6] = 0x18  # JR
    rom[0x15C7] = 0x1C  # +28 → $15E4 (on-demand loader entry)
    print(f"[2] 텍스트 렌더러: file 0x15C6  FE A1 → 18 1C  (가타카나 변환 우회)")

    # ── 3. 텍스트 문자열 패치 ────────────────────────────────────────────────
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
    print(f"[3] 텍스트 패치: {ok}개 성공, {len(err)}개 실패")
    for o, t, e in err:
        print(f"    ERR 0x{o:05X} '{t}': {e}")

    # ── 4. 출력 ─────────────────────────────────────────────────────────────
    with open(ROM_OUT, 'wb') as f:
        f.write(rom)
    print(f"\n[4] 출력: {ROM_OUT}")

    # ── 검증 ────────────────────────────────────────────────────────────────
    print("\n=== 검증 ===")
    print(f"  bank 전환: file 0x160A = 0x{rom[0x160A]:02X}  (08 = bank8)")
    print(f"  텍스트렌더러: {bytes(rom[0x15C6:0x15C8]).hex()}  (18 1C = JR +28)")
    print(f"  숫자 타일 보존 확인:")
    for digit in range(10):
        b = 0x30 + digit
        bank8_off = 0x20090 + b * 8
        tile = bytes(rom[bank8_off:bank8_off+8]).hex()
        print(f"    '{digit}' (0x{b:02X}): {tile}")
    print(f"\n  한글 인코딩 예시:")
    for ch in ['가', '사', '한', '글', '코', '스']:
        if ch in CHAR_TO_BYTE:
            b = CHAR_TO_BYTE[ch]
            bank8_off = 0x20090 + b * 8
            print(f"    '{ch}' → byte 0x{b:02X} ← bank8 file 0x{bank8_off:05X}")


if __name__ == '__main__':
    main()
