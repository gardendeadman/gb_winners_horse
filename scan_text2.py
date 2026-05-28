#!/usr/bin/env python3
"""Smarter text scanner: only accepts bytes valid for game text."""
ROM = 'Winners_Horse_Japan.gb'
with open(ROM, 'rb') as f:
    orig = bytearray(f.read())

STD = {
    0xAC:'ア',0xAD:'イ',0xAE:'ウ',0xAF:'エ',0xB0:'オ',
    0xB1:'カ',0xB2:'キ',0xB3:'ク',0xB4:'ケ',0xB5:'コ',
    0xB6:'サ',0xB7:'シ',0xB8:'ス',0xB9:'セ',0xBA:'ソ',
    0xBB:'タ',0xBC:'チ',0xBD:'ツ',0xBE:'テ',0xBF:'ト',
    0xC0:'ナ',0xC1:'ニ',0xC2:'ヌ',0xC3:'ネ',0xC4:'ノ',
    0xC5:'ハ',0xC6:'ヒ',0xC7:'フ',0xC8:'ヘ',0xC9:'ホ',
    0xCA:'マ',0xCB:'ミ',0xCC:'ム',0xCD:'メ',0xCE:'モ',
    0xCF:'ヤ',0xD0:'ユ',0xD1:'ヨ',0xD2:'ラ',0xD3:'リ',
    0xD4:'ル',0xD5:'レ',0xD6:'ロ',0xD7:'ワ',0xD8:'ン',
    0xD9:'゛',0xDA:'゜',0xA7:'ャ',0xA8:'ュ',0xA9:'ョ',
    0xAA:'ッ',0xAB:'ー',0xA2:'ァ',0xA3:'ィ',0xA4:'ゥ',0xA5:'ェ',0xA6:'ォ',
}
GAME = {k+5: v for k,v in STD.items()}
VOICED = {'カ':'ガ','キ':'ギ','ク':'グ','ケ':'ゲ','コ':'ゴ','サ':'ザ','シ':'ジ','ス':'ズ','セ':'ゼ','ソ':'ゾ',
          'タ':'ダ','チ':'ヂ','ツ':'ヅ','テ':'デ','ト':'ド','ハ':'バ','ヒ':'ビ','フ':'ブ','ヘ':'ベ','ホ':'ボ'}
SEMI = {'ハ':'パ','ヒ':'ピ','フ':'プ','ヘ':'ペ','ホ':'ポ'}

# Valid text bytes: control codes, space, digits, letters, katakana range, punctuation
def is_text_byte(b):
    if b == 0x00: return True  # end
    if b in (0x01, 0x02, 0x03): return True  # control
    if b == 0x20: return True  # space
    if b == 0x2C: return True  # comma
    if b == 0x3C: return True  # < (special char in game text)
    if b == 0x3F: return True  # ? (question mark / は particle marker)
    if 0x30 <= b <= 0x39: return True  # digits
    if 0xA1 <= b <= 0xDF: return True  # katakana range (incl. game +5 encoding)
    return False

def is_text_start(b):
    return b == 0x03  # strings start with CLR code

def decode_raw(data):
    raw = []
    for b in data:
        if b == 0x00: break
        elif b == 0x01: raw.append('[W]')
        elif b == 0x02: raw.append('\n')
        elif b == 0x03: raw.append('[C]')
        elif b == 0x20: raw.append(' ')
        elif b == 0x2C: raw.append(',')
        elif b == 0x3C: raw.append('<')
        elif b == 0x3F: raw.append('?')
        elif 0x30 <= b <= 0x39: raw.append(chr(b))
        elif b in GAME: raw.append(GAME[b])
        elif b < 0x20: raw.append(f'[{b:02X}]')
        else: raw.append(f'({b:02X})')
    result = []
    for ch in raw:
        if ch == '゛' and result:
            result[-1] = VOICED.get(result[-1], result[-1]+'゛')
        elif ch == '゜' and result:
            result[-1] = SEMI.get(result[-1], result[-1]+'゜')
        else:
            result.append(ch)
    return ''.join(result)

PATCHED = set([
    0x04F57,0x04F6D,0x04F83,0x04F99,0x04FAF,0x04FC5,0x04FDB,0x04FF1,0x05007,
    0x0501D,0x05033,0x05049,0x0505F,0x0B45A,0x0B49A,0x0B4EA,0x1814B,0x18159,
    0x18175,0x18199,0x181AA,0x181B7,0x181C7,0x181D2,0x181EF,0x18204,0x1822E,
    0x1823C,0x18276,0x18287,0x182A2,0x182B0,0x182FB,0x18325,0x1833C,0x1834A,
    0x18368,0x18422,0x1846E,0x18488,0x18504,0x18563,0x185EA,0x185F9,0x18626,
    0x1868B,0x1869C,0x186AB,0x186BA,0x186DA,0x18715,0x1873E,0x187A4,0x187D5,
    0x1880A,0x18827,0x18856,0x0B65B,0x0B663,0x0B66B,0x0B673,0x0B67B,0x0B683,
    0x0B68B,0x0B693,0x040EE,0x043DF,0x05075,0x05088,0x05E26,0x05E2A,0x05E2F,
    0x05E33,0x05E4F,0x0B55A,0x0B5D1,0x0B69B,0x0B72E,0x0B7A0,0x0B7B5,0x0B7C5,
    0x0B7D5,0x0B7E5,0x0B7F5,0x0B805,0x0B815,0x0B825,0x0B835,0x0B845,0x0B855,
    0x0B865,0x0B875,0x0B885,0x0B972,0x0BA41,0x0BA47,0x0BA4D,0x0BA53,0x0BA8D,
    0x0BAC6,0x0BCAC,0x18782,0x1E9AA,0x1E9BA,0x1E9CA,
    0x05E6F,0x05E91,0x05EB3,0x05ED4,0x05F0F,0x05F49,0x05F86,0x05FC9,0x05FFD,
    0x06045,0x06089,0x060A9,0x060C9,
])

def near_patched(off):
    return any(abs(off - p) < 50 for p in PATCHED)

# Key: only search banks 0-7 (128KB original ROM) and look for strings
# that are ENTIRELY composed of valid text bytes
results = []
i = 0
size = len(orig)  # 128KB original
while i < size:
    b = orig[i]
    if b == 0x03:  # potential text start
        # Scan forward checking all bytes are valid text
        j = i
        while j < size and orig[j] != 0x00 and (j - i) < 150:
            if not is_text_byte(orig[j]):
                break
            j += 1

        if orig[j] == 0x00 and j > i + 3:  # found complete string
            data = bytes(orig[i:j])
            kata = sum(1 for x in data if 0xA6 <= x <= 0xDF)
            text_frac = sum(1 for x in data if is_text_byte(x)) / len(data)

            if kata >= 3 and text_frac >= 0.95 and i not in PATCHED and not near_patched(i):
                bank = i // 0x4000
                decoded = decode_raw(data)
                results.append((i, bank, j - i, kata, decoded))
        i = j + 1
    else:
        i += 1

print(f'미번역 텍스트: {len(results)}개')
print()
for off, bank, length, kata, text in results:
    cpu = 0x4000 + (off % 0x4000) if bank > 0 else off
    print(f'0x{off:05X} [뱅크{bank} CPU_${cpu:04X}] len={length}')
    print(f'  {text}')
    print()
