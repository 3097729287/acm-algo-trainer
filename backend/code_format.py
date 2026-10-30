"""Local, bounded stdin formatting; never executes or uploads user programs."""
from pathlib import Path
from functools import lru_cache
import hashlib,json,os,subprocess,sys,threading
from training import ServiceError

MAX_CODE=65536
TIMEOUT=5
_slots=threading.BoundedSemaphore(2)
_verified={}
_verification_lock=threading.Lock()

@lru_cache(maxsize=1)
def _manifest():
    root=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    value=json.loads((root/'resources/code-formatters.json').read_text('utf8'))
    if value.get('schema')!=1 or set(value['tools'])!={'cpp17','python3'}:raise ValueError('Invalid formatter manifest')
    return value['tools']

def _resolve_tool(language):
    if os.name!='nt':raise ServiceError(503,'本机格式化工具暂不可用，代码已保留。')
    base=Path(sys.executable).resolve().parent/'resources/formatters' if getattr(sys,'frozen',False) else Path(os.environ.get('TB_FORMATTERS_ROOT','__absent_formatters__')).resolve()
    try:
        tool=_manifest()[language];path=base/tool['fileName']
        stat=path.stat()
        if path.resolve().parent!=base.resolve() or getattr(stat,'st_file_attributes',0)&0x400 or stat.st_size!=tool['bytes']:raise ValueError('Unexpected tool')
        key=(str(path.resolve()),stat.st_size,stat.st_mtime_ns,tool['sha256'])
        with _verification_lock:
            if key not in _verified:
                with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
                if actual!=tool['sha256']:raise ValueError('Tool digest mismatch')
                if len(_verified)>=4:_verified.clear()
                _verified[key]=True
        return path,tool
    except (OSError,ValueError,KeyError):raise ServiceError(503,'本机格式化工具暂不可用，代码已保留。') from None

def formatting_available():
    try:
        for language in ('cpp17','python3'):_resolve_tool(language)
        return True
    except (ServiceError,OSError,ValueError,KeyError):return False

def _arguments(language):
    if language=='cpp17':
        return ['--assume-filename=main.cpp','--fail-on-incomplete-format',
                '--style={BasedOnStyle: LLVM, IndentWidth: 4, ColumnLimit: 100, SortIncludes: Never, ReflowComments: false, FixNamespaceComments: false}']
    return ['format','--isolated','--no-cache','--stdin-filename=main.py','--line-length=100',
            '--target-version=py313','--config',"format.quote-style='preserve'",'-']

def _run(executable,arguments,source):
    """Drain bounded pipes concurrently so large diagnostics cannot deadlock."""
    try:process=subprocess.Popen([str(executable),*arguments],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),cwd=executable.parent)
    except OSError:raise ServiceError(503,'本机格式化工具暂不可用，代码已保留。') from None
    buffers={};overflow=threading.Event()
    def read(name,stream,limit):
        try:
            data=stream.read(limit+1);buffers[name]=data
            if len(data)>limit:
                overflow.set()
                try:process.kill()
                except OSError:pass  # The other bounded reader may already have stopped it.
        finally:stream.close()
    def write():
        try:process.stdin.write(source)
        except (BrokenPipeError,OSError):pass
        finally:
            try:process.stdin.close()
            except OSError:pass
    threads=[threading.Thread(target=read,args=('out',process.stdout,MAX_CODE),daemon=True),
             threading.Thread(target=read,args=('err',process.stderr,8192),daemon=True),
             threading.Thread(target=write,daemon=True)]
    for thread in threads:thread.start()
    try:process.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        process.kill();process.wait();raise ServiceError(408,'格式化超时，原代码已保留。') from None
    finally:
        for thread in threads:thread.join(timeout=1)
    if overflow.is_set():raise ServiceError(422,'格式化结果超过大小限制，原代码已保留。')
    if process.returncode:
        raise ServiceError(422,'代码暂时无法格式化，原内容已保留。')
    try:return buffers.get('out',b'').decode('utf8')
    except UnicodeError:raise ServiceError(422,'格式化结果无效，原代码已保留。') from None

def text_edits(before,after):
    """Linear bounded-lookahead alignment; no quadratic repeated-text diff.

    Formatters primarily change whitespace. Align nonspace characters, then
    preserve those characters while changing their gaps. Token changes such as
    Ruff's added parentheses use at most 64 characters of resynchronization.
    Offsets are JS/CodeMirror UTF-16 units, including astral Unicode characters.
    """
    if before==after:return []
    a=[i for i,c in enumerate(before) if not c.isspace()];b=[i for i,c in enumerate(after) if not c.isspace()]
    ac=''.join(before[i] for i in a);bc=''.join(after[i] for i in b)
    utf16=[0]
    for char in before:utf16.append(utf16[-1]+(2 if ord(char)>0xffff else 1))
    edits=[]
    def change(start,end,insert):
        if before[start:end]==insert:return
        if edits and edits[-1]['to']==utf16[start]:edits[-1]['to']=utf16[end];edits[-1]['insert'].append(insert)
        else:edits.append({'from':utf16[start],'to':utf16[end],'insert':[insert]})
    i=j=pa=pb=0
    while i<len(a) and j<len(b):
        if ac[i]==bc[j]:
            change(pa,a[i],after[pb:b[j]]);pa=a[i]+1;pb=b[j]+1;i+=1;j+=1;continue
        width=min(8,len(ac)-i,len(bc)-j)
        anchors={}
        for x in range(i,min(len(ac)-width+1,i+65)):
            anchors.setdefault(ac[x:x+width],x)
        best=None
        for y in range(j,min(len(bc)-width+1,j+65)):
            x=anchors.get(bc[y:y+width])
            if x is not None and (best is None or x-i+y-j<best[0]):best=(x-i+y-j,x,y)
        if best is not None:
            _,x,y=best;change(pa,a[x],after[pb:b[y]]);pa=a[x];pb=b[y];i=x;j=y
        else:
            change(pa,a[i]+1,after[pb:b[j]+1]);pa=a[i]+1;pb=b[j]+1;i+=1;j+=1
    change(pa,len(before),after[pb:])
    return [{**edit,'insert':''.join(edit['insert'])} for edit in edits]

def _check_context(training,body):
    identity=body.get('id')
    if not isinstance(identity,str) or not identity or len(identity)>512:raise ServiceError(400,'题目编号无效')
    with training.lock:
        if getattr(training,'closed',False):raise ServiceError(503,'服务正在关闭，请稍后重试')
        if body.get('contestId') or training.active_contest():raise ServiceError(409,'比赛期间不能格式化代码。')
        training._row(identity)
        training.assert_solution_unlocked(identity)

def format_code(training,body):
    if not isinstance(body,dict):raise ServiceError(400,'请求内容无效')
    language=training._language(body.get('language','cpp17'))
    try:code=training._code(body.get('code'))
    except UnicodeError:raise ServiceError(400,'代码必须是有效文本') from None
    _check_context(training,body)
    if not _slots.acquire(blocking=False):raise ServiceError(429,'正在格式化代码，请稍后重试。')
    try:
        path,tool=_resolve_tool(language)
        # Contest start uses this same lock. Recheck after resolving the fixed
        # tool, then keep its bounded execution ahead of any concurrent start.
        with training.lock:
            _check_context(training,body)
            formatted=_run(path,_arguments(language),code.encode('utf8')) if code.strip() else code
            if len(formatted.encode('utf8'))>MAX_CODE or code.strip() and not formatted.strip():raise ServiceError(422,'格式化结果无效，原代码已保留。')
            _check_context(training,body)
        return {'language':language,'code':formatted,'changes':text_edits(code,formatted),
                'inputSha256':hashlib.sha256(code.encode('utf8')).hexdigest(),
                'formatter':{'name':tool['name'],'version':tool['version']}}
    finally:_slots.release()
