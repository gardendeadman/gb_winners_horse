#!/usr/bin/env python3
"""
Winner's Horse (Japan) GBC ROM Text Extractor
Encoding: game byte - 5 = JIS X 0201 katakana (for range 0xA6-0xDF)
"""

import sys
import unicodedata
from pathlib import Path

ROM_PATH = '/home/user/gb_winners_horse/Winners_Horse_Japan.gb'

# JIS X 0201 half-width katakana table
JIS_TABLE = {
    0xA1:'ｦ',0xA2:'ｧ',0xA3:'ｨ',0xA4:'ｩ',0xA5:'ｪ',0xA6:'ｫ',0xA7:'ｬ',0xA8:'ｭ',0xA9:'ｮ',0xAA:'ｯ',
    0xAB:'ｰ',0xAC:'ｱ',0xAD:'ｲ',0xAE:'ｳ',0xAF:'ｴ',0xB0:'ｵ',0xB1:'ｶ',0xB2:'ｷ',0xB3:'ｸ',0xB4:'ｹ',
    0xB5:'ｺ',0xB6:'ｻ',0xB7:'ｼ',0xB8:'ｽ',0xB9:'ｾ',0xBA:'ｿ',0xBB:'ﾀ',0xBC:'ﾁ',0xBD:'ﾂ',0xBE:'ﾃ',
    0xBF:'ﾄ',0xC0:'ﾅ',0xC1:'ﾆ',0xC2:'ﾇ',0xC3:'ﾈ',0xC4:'ﾉ',0xC5:'ﾊ',0xC6:'ﾋ',0xC7:'ﾌ',0xC8:'ﾍ',
    0xC9:'ﾎ',0xCA:'ﾏ',0xCB:'ﾐ',0xCC:'ﾑ',0xCD:'ﾒ',0xCE:'ﾓ',0xCF:'ﾔ',0xD0:'ﾕ',0xD1:'ﾖ',0xD2:'ﾗ',
    0xD3:'ﾘ',0xD4:'ﾙ',0xD5:'ﾚ',0xD6:'ﾛ',0xD7:'ﾜ',0xD8:'ﾝ',0xD9:'ﾞ',0xDA:'ﾟ',
}

# Full-width katakana for nicer display
FW_KANA = {
    'ｦ':'ヲ','ｧ':'ァ','ｨ':'ィ','ｩ':'ゥ','ｪ':'ェ','ｫ':'ォ','ｬ':'ャ','ｭ':'ュ','ｮ':'ョ','ｯ':'ッ',
    'ｰ':'ー','ｱ':'ア','ｲ':'イ','ｳ':'ウ','ｴ':'エ','ｵ':'オ','ｶ':'カ','ｷ':'キ','ｸ':'ク','ｹ':'ケ',
    'ｺ':'コ','ｻ':'サ','ｼ':'シ','ｽ':'ス','ｾ':'セ','ｿ':'ソ','ﾀ':'タ','ﾁ':'チ','ﾂ':'ツ','ﾃ':'テ',
    'ﾄ':'ト','ﾅ':'ナ','ﾆ':'ニ','ﾇ':'ヌ','ﾈ':'ネ','ﾉ':'ノ','ﾊ':'ハ','ﾋ':'ヒ','ﾌ':'フ','ﾍ':'ヘ',
    'ﾎ':'ホ','ﾏ':'マ','ﾐ':'ミ','ﾑ':'ム','ﾒ':'メ','ﾓ':'モ','ﾔ':'ヤ','ﾕ':'ユ','ﾖ':'ヨ','ﾗ':'ラ',
    'ﾘ':'リ','ﾙ':'ル','ﾚ':'レ','ﾛ':'ロ','ﾜ':'ワ','ﾝ':'ン',
    # Dakuten combinations (half-width combined)
    'ｶﾞ':'ガ','ｷﾞ':'ギ','ｸﾞ':'グ','ｹﾞ':'ゲ','ｺﾞ':'ゴ',
    'ｻﾞ':'ザ','ｼﾞ':'ジ','ｽﾞ':'ズ','ｾﾞ':'ゼ','ｿﾞ':'ゾ',
    'ﾀﾞ':'ダ','ﾁﾞ':'ヂ','ﾂﾞ':'ヅ','ﾃﾞ':'デ','ﾄﾞ':'ド',
    'ﾊﾞ':'バ','ﾋﾞ':'ビ','ﾌﾞ':'ブ','ﾍﾞ':'ベ','ﾎﾞ':'ボ','ｳﾞ':'ヴ',
    'ﾊﾟ':'パ','ﾋﾟ':'ピ','ﾌﾟ':'プ','ﾍﾟ':'ペ','ﾎﾟ':'ポ',
}

# Known custom tile characters in the game (0x60-0x7F range)
CUSTOM_CHARS = {
    0x60:'[╔]',0x61:'[═]',0x62:'[╗]',
    0x63:'[║]',0x64:'[║]',
    0x65:'[╚]',0x66:'[═]',0x67:'[╝]',
    0x6D:'歳',  # "years old" in horse racing context
    0x7F:'杯',  # "cup/trophy"
    0xFF:'〔数字〕',  # number placeholder
}

def decode_byte(b):
    """Decode a single ROM byte to a character."""
    if b == 0x20:
        return ' '
    if 0x21 <= b <= 0x5F:
        return chr(b)
    if 0x61 <= b <= 0x7A and b not in CUSTOM_CHARS:
        # lowercase might be custom chars or literal
        return chr(b)
    if b in CUSTOM_CHARS:
        return CUSTOM_CHARS[b]
    # Japanese katakana: game byte - 5 = JIS X 0201
    if 0xA6 <= b <= 0xDF:
        jis = b - 5
        if jis in JIS_TABLE:
            return JIS_TABLE[jis]
    return f'[{b:02X}]'

def decode_raw(raw_bytes):
    """Decode bytes to half-width katakana string."""
    chars = [decode_byte(b) for b in raw_bytes]
    # Combine dakuten
    result = []
    i = 0
    DAKU = {'ｶ':'ｶﾞ','ｷ':'ｷﾞ','ｸ':'ｸﾞ','ｹ':'ｹﾞ','ｺ':'ｺﾞ',
            'ｻ':'ｻﾞ','ｼ':'ｼﾞ','ｽ':'ｽﾞ','ｾ':'ｾﾞ','ｿ':'ｿﾞ',
            'ﾀ':'ﾀﾞ','ﾁ':'ﾁﾞ','ﾂ':'ﾂﾞ','ﾃ':'ﾃﾞ','ﾄ':'ﾄﾞ',
            'ﾊ':'ﾊﾞ','ﾋ':'ﾋﾞ','ﾌ':'ﾌﾞ','ﾍ':'ﾍﾞ','ﾎ':'ﾎﾞ','ｳ':'ｳﾞ'}
    HANDAKU = {'ﾊ':'ﾊﾟ','ﾋ':'ﾋﾟ','ﾌ':'ﾌﾟ','ﾍ':'ﾍﾟ','ﾎ':'ﾎﾟ'}
    while i < len(chars):
        ch = chars[i]
        if ch == 'ﾞ' and result:
            prev = result[-1]
            result[-1] = DAKU.get(prev, prev + 'ﾞ')
        elif ch == 'ﾟ' and result:
            prev = result[-1]
            result[-1] = HANDAKU.get(prev, prev + 'ﾟ')
        else:
            result.append(ch)
        i += 1
    return ''.join(result)

def to_fullwidth(hw_str):
    """Convert half-width katakana string to full-width."""
    result = []
    i = 0
    chars = list(hw_str)
    while i < len(chars):
        c = chars[i]
        if c in FW_KANA:
            result.append(FW_KANA[c])
        else:
            result.append(c)
        i += 1
    return ''.join(result)

def has_japanese(decoded):
    """Check if decoded string has Japanese content."""
    jp_chars = set('ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ'
                  'ｶﾞｷﾞｸﾞｹﾞｺﾞｻﾞｼﾞｽﾞｾﾞｿﾞﾀﾞﾁﾞﾂﾞﾃﾞﾄﾞﾊﾞﾋﾞﾌﾞﾍﾞﾎﾞｳﾞﾊﾟﾋﾟﾌﾟﾍﾟﾎﾟ')
    return any(c in jp_chars or c in '歳杯' for c in decoded)

def extract_strings(rom_data):
    """Extract all meaningful text strings from ROM."""
    strings = []
    seen = set()
    
    i = 0
    while i < len(rom_data):
        b = rom_data[i]
        
        # Look for control codes that start text sections
        if b in (0x01, 0x02, 0x03):
            j = i + 1
            raw = []
            while j < len(rom_data) and rom_data[j] != 0x00:
                if j - i > 50:  # max string length
                    break
                raw.append(rom_data[j])
                j += 1
            
            if rom_data[j] == 0x00 and len(raw) >= 2:
                decoded = decode_raw(bytes(raw))
                decoded_stripped = decoded.strip()
                fw = to_fullwidth(decoded_stripped)
                
                if has_japanese(decoded) and len(decoded_stripped) >= 2:
                    key = fw
                    if key not in seen:
                        seen.add(key)
                        strings.append({
                            'offset': i,
                            'raw': bytes(raw),
                            'ctrl': b,
                            'decoded': decoded,
                            'fullwidth': fw,
                        })
            i = j + 1
            continue
        
        # Also look for standalone null-terminated strings with Japanese
        if 0xA6 <= b <= 0xDF or (0x20 <= b <= 0x7E):
            j = i
            raw = []
            while j < len(rom_data) and rom_data[j] != 0x00:
                if j - i > 40:
                    break
                raw.append(rom_data[j])
                j += 1
            
            if rom_data[j] == 0x00 and len(raw) >= 3:
                decoded = decode_raw(bytes(raw))
                decoded_stripped = decoded.strip()
                fw = to_fullwidth(decoded_stripped)
                
                if has_japanese(decoded) and len(decoded_stripped) >= 3:
                    key = fw
                    if key not in seen:
                        seen.add(key)
                        strings.append({
                            'offset': i,
                            'raw': bytes(raw),
                            'ctrl': None,
                            'decoded': decoded,
                            'fullwidth': fw,
                        })
        
        i += 1
    
    return strings

def main():
    rom_data = Path(ROM_PATH).read_bytes()
    print(f'ROM size: {len(rom_data)} bytes')
    
    strings = extract_strings(rom_data)
    
    print(f'\nFound {len(strings)} unique Japanese text strings\n')
    print('=' * 80)
    print(f'{"Offset":<10} {"Japanese (Full-width)":<35} {"Korean Translation"}')
    print('=' * 80)
    
    for s in strings:
        offset_str = f'0x{s["offset"]:05X}'
        jp = s['fullwidth']
        print(f'{offset_str:<10} {jp:<35} [번역 필요]')
    
    # Save to file
    with open('/home/user/gb_winners_horse/extracted_strings.txt', 'w', encoding='utf-8') as f:
        f.write('Winner\'s Horse (Japan) - 추출된 텍스트\n')
        f.write('인코딩: JIS X 0201 카타카나 + 5 오프셋\n')
        f.write('=' * 80 + '\n\n')
        
        for s in strings:
            f.write(f'오프셋: 0x{s["offset"]:05X}\n')
            f.write(f'원본 바이트: {s["raw"].hex()}\n')
            f.write(f'일본어: {s["fullwidth"]}\n')
            f.write(f'한국어 번역: \n')
            f.write('-' * 40 + '\n')
    
    print(f'\n파일 저장: /home/user/gb_winners_horse/extracted_strings.txt')

if __name__ == '__main__':
    main()
