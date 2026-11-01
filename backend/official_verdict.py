"""Keep judge-supplied diagnostics separate from the normalized result code."""
import re

CF_LABELS={'WRONG_ANSWER':'Wrong answer','TIME_LIMIT_EXCEEDED':'Time limit exceeded',
           'MEMORY_LIMIT_EXCEEDED':'Memory limit exceeded','RUNTIME_ERROR':'Runtime error',
           'COMPILATION_ERROR':'Compilation error','OUTPUT_LIMIT_EXCEEDED':'Output limit exceeded'}


def codeforces_detail(record):
    label=CF_LABELS.get(record.get('verdict'))
    if not label:return ''
    passed=record.get('passedTestCount');testset=record.get('testset')
    if type(passed) is int and 0<=passed<100000 and testset in {'TESTS','PRETESTS','SAMPLES'} and record.get('verdict')!='COMPILATION_ERROR':
        kind={'TESTS':'test','PRETESTS':'pretest','SAMPLES':'sample'}[testset]
        return f'{label} on {kind} {passed+1}'
    return label


def receipt_detail(receipt):
    value=receipt.get('verdictDetail') or receipt.get('detail')
    if not isinstance(value,str):
        message=receipt.get('message')
        value=message if isinstance(message,str) and re.search(r'wrong|\bon (?:pretest|test)\b|limit exceeded|runtime error|compilation error|错误|测试点|编译失败',message,re.I) else ''
    value=re.sub(r'[\x00-\x1f\x7f]+',' ',value).strip()[:500]
    return value if len(value)>4 and value!=receipt.get('verdict') else ''


def saved_detail(message,scope):
    return message.split('\n',1)[1][:500] if scope=='official' and isinstance(message,str) and '\n' in message else ''
