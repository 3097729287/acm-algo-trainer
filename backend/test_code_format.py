from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,importlib.util,json,random,shutil,sys,tempfile,threading,time,unittest
import code_format as F
from training import ServiceError

def training(active=None):
    def code(value):
        if not isinstance(value,str) or len(value.encode('utf8'))>F.MAX_CODE:raise ServiceError(400,'code')
        return value
    def language(value):
        if value not in ('cpp17','python3'):raise ServiceError(400,'language')
        return value
    return SimpleNamespace(lock=threading.RLock(),closed=False,_code=code,_language=language,_row=lambda identity:None,
                           active_contest=lambda:active,assert_solution_unlocked=lambda identity:None)

def apply_edits(source,edits):
    value=source.encode('utf-16-le')
    for edit in reversed(edits):value=value[:edit['from']*2]+edit['insert'].encode('utf-16-le')+value[edit['to']*2:]
    return value.decode('utf-16-le')

class FormattingTests(unittest.TestCase):
    def test_contest_context_and_actual_active_contest_never_resolve_or_run_tools(self):
        for service,context in [(training(),{'contestId':'mock'}),(training({'status':'running'}),{}),(training(),{'contestId':'formal'})]:
            with patch.object(F,'_resolve_tool') as tool,patch.object(F,'_run') as run,self.assertRaises(ServiceError) as failure:
                F.format_code(service,dict(id='fixture',language='cpp17',code='int x;',**context))
            self.assertEqual(failure.exception.status,409);tool.assert_not_called();run.assert_not_called()

    def test_contest_starting_during_formatting_discards_the_result(self):
        service=training();body={'id':'fixture','code':'int x=1;','language':'cpp17'}
        def run(*_):service.active_contest=lambda:{'status':'running'};return 'int x = 1;'
        with patch.object(F,'_resolve_tool',return_value=(Path('fixture'),{'name':'test','version':'1'})),patch.object(F,'_run',side_effect=run),self.assertRaises(ServiceError) as failure:F.format_code(service,body)
        self.assertEqual(failure.exception.status,409)

    def test_real_contest_start_waits_for_bounded_formatter_execution(self):
        from training import TrainingService
        from test_training import Library,Assets,Judge,Clock
        directory=Path(tempfile.mkdtemp(prefix='tb-format-contest-'))
        library=Library();judge=Judge();service=TrainingService(library,directory/'personal.sqlite3',Assets(library),judge,Clock(),directory/'backups')
        entered=threading.Event();release=threading.Event();starting=threading.Event();started=threading.Event()
        answers=[];contests=[];errors=[];workers=[]
        try:
            plan=service.preview_contest({'count':1,'duration':120,'min':1000,'max':2100})['plan']
            def run(*_):
                entered.set()
                if not release.wait(2):raise AssertionError('Bounded formatter fixture was not released')
                self.assertIsNone(service.active_contest(),'A contest must not become active during native formatting')
                return 'int x = 1;'
            def format_request():
                try:answers.append(F.format_code(service,{'id':'fixture::A','language':'cpp17','code':'int x=1;'}))
                except BaseException as error:errors.append(error)
            def start_request():
                starting.set()
                try:contests.append(service.start_contest({'ids':[slot['id'] for slot in plan['slots']],'duration':plan['duration'],'previewId':plan['previewId']}))
                except BaseException as error:errors.append(error)
                finally:started.set()
            with patch.object(F,'_resolve_tool',return_value=(Path('fixture'),{'name':'fixture','version':'1'})),patch.object(F,'_run',side_effect=run):
                formatter=threading.Thread(target=format_request,daemon=True);workers.append(formatter);formatter.start()
                self.assertTrue(entered.wait(2))
                starter=threading.Thread(target=start_request,daemon=True);workers.append(starter);starter.start()
                self.assertTrue(starting.wait(1))
                try:self.assertFalse(started.wait(.15),'Real TrainingService.start_contest must wait for the formatter lock')
                finally:release.set()
                for worker in workers:worker.join(3)
                self.assertFalse(any(worker.is_alive() for worker in workers),'Concurrent requests must finish within a bounded deadline')
            self.assertEqual(errors,[]);self.assertEqual(answers[0]['code'],'int x = 1;')
            self.assertEqual(len(contests),1);self.assertIsNotNone(service.active_contest())
        finally:
            release.set()
            for worker in workers:worker.join(3)
            judge.release.set();service.close()
            print(json.dumps({'retainedTestArtifacts':str(directory)}))

    def test_contest_starting_while_resolving_tool_never_executes_it(self):
        service=training()
        def resolve(_):
            service.active_contest=lambda:{'status':'running'}
            return Path('fixture'),{'name':'fixture','version':'1'}
        with patch.object(F,'_resolve_tool',side_effect=resolve),patch.object(F,'_run') as run,self.assertRaises(ServiceError) as failure:
            F.format_code(service,{'id':'fixture','language':'cpp17','code':'int x=1;'})
        self.assertEqual(failure.exception.status,409);run.assert_not_called()

    def test_invalid_language_source_size_and_closed_service_do_not_run_tools(self):
        cases=[{'language':'shell','code':'x'},{'language':'cpp17','code':'x'*(F.MAX_CODE+1)},{'language':'cpp17','code':None}]
        for body in cases:
            with patch.object(F,'_resolve_tool') as tool,self.assertRaises(ServiceError):F.format_code(training(),dict(id='fixture',**body))
            tool.assert_not_called()
        service=training();service.closed=True
        with patch.object(F,'_resolve_tool') as tool,self.assertRaises(ServiceError):F.format_code(service,{'id':'fixture','code':'x','language':'cpp17'})
        tool.assert_not_called()

    def test_utf16_edits_reconstruct_chinese_emoji_and_parenthesis_changes(self):
        pairs=[('// 中文 😀\nint x=1;\n','// 中文 😀\nint x = 1;\n'),('x=1\nif x:print(x)','x = 1\nif x:\n    print(x)\n'),('f(a, b)','f((a), b)'),('"引号😀"','\'引号😀\'')]
        rng=random.Random(11)
        for _ in range(100):
            before=''.join(rng.choice('abc  \n😀中文;()') for _ in range(80))
            after=''.join(rng.choice('abc  \n😀中文;()') for _ in range(80));pairs.append((before,after))
        for before,after in pairs:self.assertEqual(apply_edits(before,F.text_edits(before,after)),after)

    def test_64k_repeated_text_diff_is_bounded_and_coalesced(self):
        before='a'*F.MAX_CODE;after='b'*F.MAX_CODE;start=time.monotonic();changes=F.text_edits(before,after)
        self.assertEqual(apply_edits(before,changes),after);self.assertEqual(len(changes),1)
        self.assertLess(time.monotonic()-start,5,'Bounded lookahead must not become an unbounded quadratic repeated-text diff')

    def test_runner_bounds_stdout_stderr_and_timeout(self):
        for program in [f'import sys;sys.stdout.write("x"*{F.MAX_CODE+1})','import sys;sys.stderr.write("x"*9000)']:
            with self.assertRaises(ServiceError) as failure:F._run(Path(sys.executable),['-c',program],b'')
            self.assertEqual(failure.exception.status,422)
        with patch.object(F,'TIMEOUT',.1),self.assertRaises(ServiceError) as failure:F._run(Path(sys.executable),['-c','import time;time.sleep(5)'],b'')
        self.assertEqual(failure.exception.status,408)

    @unittest.skipUnless(F.formatting_available(),'Pinned Windows formatters are not installed in this source/CI environment')
    def test_packaged_copy_resolves_and_runs_without_path_or_download(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('tb_formatter_packaging',root/'scripts/prepare_formatters.py')
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        import os
        directory=tempfile.mkdtemp(prefix='tb-format-package-')
        try:
            package=Path(directory)/'package';target=helper.copy_to_package(os.environ['TB_FORMATTERS_ROOT'],package)
            shutil.copy2(root/'backend/resources/code-formatters.json',package/'resources/code-formatters.json')
            self.assertEqual(target,package/'resources/formatters')
            self.assertFalse((package/'formatters').exists());self.assertEqual(len(list((target/'licenses').iterdir())),3)
            F._manifest.cache_clear()
            try:
                with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(package/'ToBe.exe')),patch.dict(os.environ,{'TB_FORMATTERS_ROOT':'__not_used_in_package__','PATH':''}):
                    self.assertTrue(F.formatting_available())
                    result=F.format_code(training(),{'id':'fixture','code':'x=1\n','language':'python3'})
                    self.assertEqual(result['code'],'x = 1\n')
            finally:F._manifest.cache_clear()
        finally:
            # Retain for inspection and authorized Recycle Bin cleanup rather
            # than using TemporaryDirectory's permanent recursive deletion.
            print(json.dumps({'retainedTestArtifacts':directory}))

    @unittest.skipUnless(F.formatting_available(),'Pinned Windows formatters are not installed in this source/CI environment')
    def test_real_cpp_and_python_tools_format_offline_and_reject_invalid_code(self):
        for language,source,expected in [('cpp17','// 中文 😀\nint x=1;\n','// 中文 😀\nint x = 1;\n'),('python3','x=1\nif x: print( x )','x = 1\nif x:\n    print(x)\n')]:
            answer=F.format_code(training(),{'id':'fixture','code':source,'language':language})
            self.assertEqual(answer['code'],expected);self.assertEqual(apply_edits(source,answer['changes']),expected)
            self.assertEqual(answer['inputSha256'],hashlib.sha256(source.encode('utf8')).hexdigest())
        with self.assertRaises(ServiceError):F.format_code(training(),{'id':'fixture','code':'def (','language':'python3'})

if __name__=='__main__':unittest.main()
