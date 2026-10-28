"""Narrow, reviewed statement differences for six published CF mirrors.

This is evidence verification, not fuzzy matching or a rule for new imports.
Only the listed pairs may omit the exact non-algorithmic clarifications below.
"""
import html
import re
import unicodedata

REVIEWED_PAIRS={
    'remote:codeforces:102348::I':('luogu-training-CF1215F',1215,'F'),
    'remote:codeforces:103993::J':('remote:codeforces:1743::D',1743,'D'),
    'remote:codeforces:105437::L':('remote:codeforces:2025::G',2025,'G'),
    'remote:codeforces:104015::K':('remote:codeforces:1598::E',1598,'E'),
    'remote:codeforces:104777::D':('remote:codeforces:1895::E',1895,'E'),
    'remote:codeforces:104777::B':('remote:codeforces:1895::G',1895,'G'),
}
OMISSIONS={
    'remote:codeforces:103993::J':('Hacks are forbidden in this problem.',),
    'remote:codeforces:105437::L':(' If an artifact is not held by any hero, it is inactive from the beginning of the battle.',),
    'remote:codeforces:104015::K':(' The rows are numbered top to bottom, the columns are numbered left to right.',),
    'remote:codeforces:104777::D':(
        ' It implies that each player always has the same set of cards to play as at the start of the game.',
        ', and the current player loses',
    ),
}

def canonical_reviewed_statement(problem_id,markdown):
    if problem_id not in REVIEWED_PAIRS:
        raise ValueError('Statement pair has not been reviewed')
    text=markdown.replace('\r','')
    text=re.sub(r'(?m)^# [^\n]*\n','',text,count=1)
    if problem_id=='remote:codeforces:104777::B':
        # Only the explanatory examples added to this one primary are omitted.
        text=text.split('\n## Note\n',1)[0]
    for sentence in OMISSIONS.get(problem_id,()):
        text=text.replace(sentence,'')
    if problem_id=='remote:codeforces:104777::D':
        text=text.replace("if a player has a winning strategy regardless of his opponent's moves, he plays for a win. Otherwise, if he has a drawing strategy, he plays for a draw.",
                          "if they have a winning strategy regardless of their opponent's moves, they play for a win. Otherwise, if they have a drawing strategy, they play for a draw.")
    text=re.sub(r'(?m)^#{1,6}\s*(?:Input|Output|题目描述|输入格式|输出格式)\s*\n','',text)
    text=text.replace('$','').replace('\\lt','<')
    for source,target in (('\\leq','≤'),('\\le','≤'),('\\geq','≥'),('\\ge','≥')):
        text=text.replace(source,target)
    return re.sub(r'\s+','',unicodedata.normalize('NFKC',html.unescape(text)))

def canonical_samples(samples):
    return [(' '.join(s['input'].split()),' '.join(s['output'].split())) for s in samples or []]
