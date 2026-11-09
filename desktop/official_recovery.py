"""Read-only recovery proofs for persisted native submissions.

No credentials or code leave the original page. Legacy code is compared by a
digest from its original observer context, rather than the editable DOM buffer.
"""
import hashlib
from urllib.parse import urlsplit


def source_hash(code):
    return hashlib.sha256(str(code).replace('\r\n', '\n').strip().encode('utf-8')).hexdigest()


def nowcoder_binding(value, url):
    if not isinstance(value, dict) or value.get('version') != 1 or value.get('platform') != '牛客':
        return None
    owner = str(value.get('owner') or '')
    identity = value.get('identity')
    query = value.get('query')
    if not owner.isdecimal() or int(owner) <= 0 or not isinstance(identity, dict) or not isinstance(query, dict):
        return None
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'ac.nowcoder.com' or parsed.query or parsed.fragment:
        return None
    if identity.get('originalUrl') != url or identity.get('kind') != 'global':
        return None
    problem = str(identity.get('problemId') or '')
    question = str(identity.get('questionId') or '')
    if not problem.isdecimal() or not question.isdecimal() or int(problem) <= 0 or int(question) <= 0 or parsed.path != '/acm/problem/'+problem:
        return None
    origin = value.get('origin')
    path = value.get('statusPath')
    if (origin, path) not in {('https://ac.nowcoder.com', '/nccommon/status'),
                              ('https://ac.nowcoder.com', '/status'),
                              ('https://victorinox.nowcoder.com', '/api/service/judge/submit-status')}:
        return None
    if set(query)-{'tagId','subTagId','userId','appId','submitType'} or str(query.get('tagId')) != '4':
        return None
    if origin == 'https://ac.nowcoder.com' and str(query.get('subTagId')) != '0':
        return None
    if origin == 'https://victorinox.nowcoder.com' and any(str(query.get(k)) != v for k,v in {'userId':owner,'appId':'6','submitType':'1'}.items()):
        return None
    return {'version':1,'platform':'牛客','owner':owner,
            'identity':{'kind':'global','problemId':problem,'questionId':question,'originalUrl':url},
            'origin':origin,'statusPath':path,'query':{k:str(v) for k,v in query.items()}}


_PROBE = """(()=>{const s=window.__tbNowcoder,p=s?.pending;if(!p)return null;
const u=s.statusUrl&&new URL(s.statusUrl),q={};
for(const k of ['tagId','subTagId','userId','appId','submitType'])if(u?.searchParams.has(k))q[k]=u.searchParams.get(k);
return {sessionId:s.sessionId,submissionId:p.submissionId,ownerMatches:String(window.globalInfo?.ownerId)===p.owner,
 currentUrl:location.origin+location.pathname,questionId:String(window.pageInfo?.questionId||''),problemId:String(window.pageInfo?.problemId||''),
 binding:{version:1,platform:'牛客',owner:p.owner,identity:p.identity,origin:u?.origin,statusPath:u?.pathname,query:q}};})()"""


def legacy_nowcoder_proof(page, record):
    """Adopt only an existing exact owned observer; never infer an old owner."""
    proof = page.evaluate(_PROBE)
    if (not isinstance(proof, dict) or proof.get('sessionId') != record['sessionId']
            or str(proof.get('submissionId')) != record['submissionId'] or not proof.get('ownerMatches')
            or proof.get('currentUrl') != record['url']):
        return None
    binding = nowcoder_binding(proof.get('binding'), record['url'])
    if not binding or any(proof.get(k) != binding['identity'][k] for k in ('problemId','questionId')):
        return None
    # Old observers did not expose their immutable submitted source. Read only
    # the matching closure's digest and language through CDP, never its code.
    function = page.call('Runtime.evaluate', {'expression':'window.__tbNowcoder.poll'})['result']
    props = page.call('Runtime.getProperties', {'objectId':function['objectId'],'ownProperties':True})
    scopes = next((p['value']['objectId'] for p in props.get('internalProperties',[]) if p['name']=='[[Scopes]]'),None)
    if not scopes:
        return None
    for scope in page.call('Runtime.getProperties', {'objectId':scopes,'ownProperties':True}).get('result',[]):
        if not scope.get('name','').isdecimal() or not scope.get('value',{}).get('objectId'):
            continue
        variables = page.call('Runtime.getProperties', {'objectId':scope['value']['objectId'],'ownProperties':True})
        context = next((p.get('value',{}).get('objectId') for p in variables.get('result',[]) if p['name']=='ctx'),None)
        if not context:
            continue
        result = page.call('Runtime.callFunctionOn', {'objectId':context,'awaitPromise':True,'returnByValue':True,
            'functionDeclaration':"""async function(){const code=String(this.code||'').replace(/\\r\\n/g,'\\n').trim();
            const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(code));
            return {sessionId:this.sessionId,url:this.originalUrl,language:this.language||'cpp17',
            sourceHash:[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('')};}"""}).get('result',{}).get('value')
        if (not isinstance(result,dict) or result.get('sessionId')!=record['sessionId'] or result.get('url')!=record['url']
                or result.get('sourceHash')!=source_hash(record['code']) or result.get('language') not in ('cpp17','python3')):
            return None
        return {'binding':binding,'language':result['language']}
    return None
