"""Correct a Chinese mathematical role only when the source explicitly proves it."""
import re

MATH=r'\${1,3}[^$\n]+\${1,3}'
SOURCE=re.compile(r'\b(?:array|string|sequence)\s+('+MATH+r')\s+(?:(?:of|with)\s+(?:length|size)\s+|(?:consisting\s+of|of|containing)\s+)('+MATH+r')',re.I)
TARGET=re.compile(r'长度为\s*('+MATH+r')\s*的(?:(?:整数|正整数|非负整数|二进制|一个|一维|二维))*?(?:数组|字符串|序列)\s*('+MATH+r')')
ELEMENTS=re.compile(r'(?:由|包含|含有)\s*('+MATH+r')\s*个(?:正|非负|不同的|互不相同的)?整数(?:组成|构成)?的(?:数组|序列)\s*('+MATH+r')')

def key(formula):return re.sub(r'\s+','',formula.strip('$'))

def repair(original,translated):
    if not isinstance(translated,str):return translated,[]
    declarations={(key(name),key(length)) for name,length in SOURCE.findall(original or '')};changes=[]
    def replace(match):
        wrong_length,wrong_name=match[1],match[2]
        pair=(key(wrong_length),key(wrong_name))
        if pair[0]==pair[1] or pair not in declarations or pair[::-1] in declarations:return match[0]
        fixed=match[0][:match.start(1)-match.start()]+wrong_name+match[0][match.end(1)-match.start():match.start(2)-match.start()]+wrong_length+match[0][match.end(2)-match.start():]
        changes.append({'before':match[0],'after':fixed});return fixed
    translated=ELEMENTS.sub(replace,TARGET.sub(replace,translated))
    phrase='在当前数组中从左数第一次和从右数最后一次出现的位置'
    if 'leftmost and rightmost occurrences' in (original or '') and phrase in translated:
        fixed='在当前数组中第一次和最后一次出现的下标';translated=translated.replace(phrase,fixed);changes.append({'before':phrase,'after':fixed})
    return translated,changes
