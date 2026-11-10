"""Account-free native input tests; no browser, profile or network access."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from native_activity import NativeActivity
from native_shortcuts import NativeShortcuts, windows_combination
import native_activity_host as module


REGISTRATION = {'serial': 1, 'bindings': [
    {'route': 'workbench', 'id': 'next', 'combo': 'Ctrl+ArrowRight', 'context': 'A'}]}
METRICS = {}


class PythonInputTests(unittest.TestCase):
    def test_initialization_failure_is_observable_without_hook_fallback(self):
        shortcuts = NativeShortcuts()
        shortcuts.configure(REGISTRATION, 'owner', 'view')
        activity = NativeActivity(shortcuts=shortcuts)
        with patch.object(module, 'managed_type', side_effect=RuntimeError('synthetic')), self.assertLogs('tb.native_input', 'WARNING'):
            activity._run()
        self.assertTrue(activity.ready.is_set())
        self.assertFalse(activity.snapshot()['available'])
        self.assertEqual(activity.diagnostics()['errorCode'], 'NATIVE_INPUT_INITIALIZATION_FAILED')
        self.assertEqual(shortcuts.snapshot('owner')['errorCode'], 'NATIVE_INPUT_INITIALIZATION_FAILED')
        self.assertFalse(shortcuts.snapshot('owner')['available'])
        self.assertEqual(shortcuts.snapshot('owner')['actions'], [])

    def test_hidden_pane_stops_ownership_watchdog_without_disposing_profile(self):
        from embedded_deepseek import DeepSeekPane
        from types import SimpleNamespace
        calls = []
        pane = DeepSeekPane(SimpleNamespace(), lambda: None, Path('unused-account-free-path'))
        pane.timer = SimpleNamespace(Stop=lambda: calls.append('stop'))
        pane.panel = SimpleNamespace(IsDisposed=False, Visible=True)
        pane._hide()
        self.assertEqual(calls, ['stop'])
        self.assertFalse(pane.panel.Visible)
        self.assertIsNotNone(pane.panel)

    def test_existing_python_callback_can_wait_on_a_busy_consumer_lock(self):
        # The original native hook called this unchanged Python key() method.
        # This is a synthetic contention proof, not a trace of the user's PC.
        shortcuts = NativeShortcuts()
        shortcuts.configure(REGISTRATION, 'owner', 'view')
        entered, done = threading.Event(), threading.Event()
        duration = []
        def callback():
            entered.set()
            start = time.perf_counter()
            shortcuts.key(39, 0, child_owned=True, control=True)
            duration.append(time.perf_counter() - start)
            done.set()
        with shortcuts.lock:
            thread = threading.Thread(target=callback)
            thread.start()
            self.assertTrue(entered.wait(.5))
            self.assertFalse(done.wait(.08))
        thread.join(.5)
        self.assertTrue(done.is_set())
        self.assertGreaterEqual(duration[0], .07)
        METRICS['pythonCallbackContendedSeconds'] = round(duration[0], 6)


@unittest.skipUnless(os.name == 'nt', 'Windows managed input host')
class ManagedInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # CLR can retain a loaded public DLL until process exit on Windows.
        cls.temp = tempfile.TemporaryDirectory(prefix='ToBe-native-input-unit-', ignore_cleanup_errors=True)
        cls.assembly = Path(cls.temp.name) / 'native-input-host.dll'
        start = time.perf_counter()
        cls.metadata = module.build(cls.assembly)
        METRICS['publicAssemblyCompileSeconds'] = round(time.perf_counter() - start, 6)
        with patch('paths.resource', return_value=cls.assembly):
            cls.Host = module.managed_type()
        import clr
        from System import Array, String
        cls.array = staticmethod(lambda values: Array[String](values))
        # A managed worker proves input production cannot wait for Python's
        # GIL, locks or a blocked sender. No Python delegates run on this thread.
        source = r'''
using System;using System.Diagnostics;using System.Reflection;using System.Threading;
using System.Windows.Forms;using ToBe.NativeInput;
namespace ToBe.InputTest {
 public sealed class Worker {
  readonly Host host;Thread thread;public volatile bool Done;public double Seconds;
  public Worker(Host value){host=value;}
  public void Start(){thread=new Thread(Run);thread.IsBackground=true;thread.Start();}
  void Run(){var timer=Stopwatch.StartNew();for(int i=0;i<20000;i++){host.Capture(39,0,true,true,false,false,false,host.ClockNow());host.Capture(39,128,true,true,false,false,false,host.ClockNow());}Seconds=timer.Elapsed.TotalSeconds;Done=true;}
  public bool Wait(int ms){return thread.Join(ms);}
 }
 public static class Lifecycle {
  public static bool Run(){bool passed=false;Exception error=null;Thread thread=new Thread(()=>{
   try {using(Form form=new Form()){TextBox main=new TextBox();form.Controls.Add(main);long handle=form.Handle.ToInt64();long child=main.Handle.ToInt64();
    using(Host host=new Host(handle,child)){host.Configure(new string[0],1,false,1);host.Start();if(!host.WaitReady(2000)||!host.Snapshot().Available)throw new Exception("HOOK_SETUP");Thread.Sleep(120);host.Dispose();
     Thread hook=(Thread)typeof(Host).GetField("thread",BindingFlags.Instance|BindingFlags.NonPublic).GetValue(host);
     passed=!form.Visible&&!host.Snapshot().Available&&!hook.IsAlive;host.Start();passed=passed&&!hook.IsAlive;}
   }}catch(Exception issue){error=issue;}});thread.SetApartmentState(ApartmentState.STA);thread.Start();if(!thread.Join(4000))throw new Exception("FIXTURE_TIMEOUT");if(error!=null)throw error;return passed;}
 }
}
'''
        provider_type, parameter_type = module._provider()
        provider, parameters = provider_type(), parameter_type()
        parameters.GenerateInMemory = True
        for reference in ('System.dll', 'System.Core.dll', 'System.Windows.Forms.dll', str(cls.assembly)):
            parameters.ReferencedAssemblies.Add(reference)
        result = provider.CompileAssemblyFromSource(parameters, source)
        if result.Errors.HasErrors:
            raise AssertionError(str(result.Errors[0].ErrorText))
        clr.AddReference(result.CompiledAssembly.FullName)
        from ToBe.InputTest import Worker, Lifecycle
        cls.Worker, cls.Lifecycle = Worker, Lifecycle

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.host = self.Host(0, 0)

    def tearDown(self):
        self.host.Dispose()

    def configure(self, keys=('ctrl+arrowright',), serial=1, active=True, generation=1):
        self.host.Configure(self.array(keys), serial, active, generation)

    def press(self, key=39, flags=0, child=True, control=True, alt=False, shift=False, meta=False):
        return self.host.Capture(key, flags, child, control, alt, shift, meta, self.host.ClockNow())

    def test_prebuilt_assembly_hash_and_once_per_process_loading(self):
        self.assertEqual(self.metadata['sourceSha256'], module.SOURCE_SHA256)
        self.assertEqual(self.metadata['assemblySha256'], hashlib.sha256(self.assembly.read_bytes()).hexdigest())
        with patch.object(module, '_provider', side_effect=AssertionError('must not compile twice')):
            self.assertIs(module.managed_type(), self.Host)

    def test_missing_or_corrupt_prebuilt_manifest_fails_closed(self):
        # Reset only the loader's Python cache; no hooks or application exist.
        original = module._type
        try:
            module._type = None
            with tempfile.TemporaryDirectory(prefix='ToBe-native-input-bad-') as folder:
                path = Path(folder) / 'native-input-host.dll'
                path.write_bytes(b'public-synthetic')
                with patch('paths.resource', return_value=path), self.assertRaisesRegex(RuntimeError, 'INCOMPLETE'):
                    module.managed_type()
                path.with_suffix('.json').write_text('{}', encoding='utf-8')
                with patch('paths.resource', return_value=path), self.assertRaisesRegex(RuntimeError, 'HASH_MISMATCH'):
                    module.managed_type()
        finally:
            module._type = original

    def test_all_windows_key_combinations_match_existing_application_normalization(self):
        for key, modifiers in itertools.product(range(256), itertools.product((False, True), repeat=4)):
            control, alt, shift, meta = modifiers
            expected = windows_combination(key, control=control, alt=alt, shift=shift, meta=meta)
            actual = self.Host.Combination(key, control, alt, shift, meta)
            self.assertEqual(actual, expected, (key, modifiers))

    def test_foreign_focus_injected_meta_and_unregistered_keys_are_not_swallowed(self):
        self.configure()
        self.assertFalse(self.press(child=False))
        for flags in (2, 16, 18, 146):
            self.assertFalse(self.press(flags=flags))
        self.assertFalse(self.press(meta=True))
        self.assertFalse(self.press(key=65, control=False))
        self.assertFalse(self.press(key=82))
        self.assertEqual(len(self.host.Commands()), 0)

    def test_repeat_pause_and_registration_changes_cannot_repeat_a_held_action(self):
        self.configure()
        for _ in range(10):
            self.assertTrue(self.press())
        self.assertEqual(len(self.host.Commands()), 1)
        self.configure(active=False, generation=2)
        self.configure(serial=2, generation=3)
        self.assertTrue(self.press())
        self.assertEqual(len(self.host.Commands()), 1)
        self.assertFalse(self.press(flags=128, child=False))
        self.assertTrue(self.press())
        self.assertEqual(len(self.host.Commands()), 2)
        self.configure(keys=('ctrl+r',), generation=2)  # late old configuration
        self.assertTrue(self.press(flags=128))
        self.assertTrue(self.press())
        self.assertFalse(self.press(key=82))

    def test_managed_queue_remains_32_while_python_and_sender_are_blocked(self):
        shortcuts = NativeShortcuts()
        shortcuts.configure(REGISTRATION, 'owner', 'view')
        shortcuts.attach_native(self.host)
        worker = self.Worker(self.host)
        # No sender exists on the production path; a blocked consumer lock and
        # an unyielding Python loop are stricter than a blocked HTTP/UI sender.
        with shortcuts.lock:
            worker.Start()
            deadline = time.perf_counter() + .15
            while time.perf_counter() < deadline:
                pass
            self.assertTrue(worker.Done)
        self.assertTrue(worker.Wait(500))
        self.assertEqual(len(self.host.Commands()), 32)
        self.assertEqual(int(self.host.Commands()[-1].Sequence), 20000)
        self.assertLess(worker.Seconds, .15)
        METRICS['managedCommands'] = 20000
        METRICS['managedProducerSecondsWhilePythonBlocked'] = round(worker.Seconds, 6)
        state = shortcuts.snapshot('owner')
        self.assertEqual(len(state['actions']), 32)
        self.assertEqual(state['sequence'], 32)
        self.assertEqual(shortcuts.snapshot('owner')['sequence'], 32)

    def test_queued_commands_do_not_cross_owner_context_or_replay_after_pause(self):
        shortcuts = NativeShortcuts()
        shortcuts.configure(REGISTRATION, 'owner-A', 'view-A')
        shortcuts.attach_native(self.host)
        self.press()
        shortcuts.configure(REGISTRATION, 'owner-B', 'view-B')
        self.assertFalse(shortcuts.snapshot('owner-B')['actions'])
        self.press(flags=128)
        self.press()
        self.assertEqual(len(shortcuts.snapshot('owner-B')['actions']), 1)
        shortcuts.pause()
        self.assertFalse(shortcuts.snapshot('owner-B')['actions'])
        shortcuts.configure(REGISTRATION, 'owner-B', 'view-B')
        self.assertFalse(shortcuts.snapshot('owner-B')['actions'])

    def test_activity_snapshot_preserves_event_age_and_tick_wrap(self):
        self.assertAlmostEqual(self.Host.Age(10, 0xfffffff0), .026)
        import System.Reflection as Reflection
        record = self.host.GetType().GetMethod('Record', Reflection.BindingFlags.Instance | Reflection.BindingFlags.NonPublic)
        from System import Array, Object, UInt32
        def observe(tick):
            record.Invoke(self.host, Array[Object]([UInt32(tick)]))
        now = int(self.host.ClockNow())
        observe(now)
        first = self.host.Snapshot()
        observe((now - 100) & 0xffffffff)
        self.assertEqual(self.host.Snapshot().Revision, first.Revision)
        time.sleep(.03)
        self.assertGreaterEqual(self.host.Snapshot().AgeSeconds, .02)
        activity = NativeActivity()
        activity.native = self.host
        self.assertEqual(set(activity.snapshot()), {'available', 'session', 'revision', 'observed', 'ageSeconds'})
        self.host.Dispose()
        observe(int(self.host.ClockNow()))
        self.assertEqual(self.host.Snapshot().Revision, first.Revision)

    def test_real_hidden_account_free_window_installs_and_releases_both_hooks(self):
        # This creates only our hidden Form/TextBox; never activates or controls
        # an existing window and registers no keys. No account/profile/Internet.
        self.assertTrue(self.Lifecycle.Run())

    def test_close_before_start_releases_waiter_without_installing_hooks(self):
        self.host.Dispose()
        self.host.Start()
        self.assertTrue(self.host.WaitReady(0))
        self.assertFalse(self.host.Snapshot().Available)
        self.assertFalse(self.press())


if __name__ == '__main__':
    result = unittest.main(exit=False)
    print(json.dumps({'nativeInputMetrics': METRICS, 'ordinaryApplicationTouched': False,
                      'networkRequests': 0, 'physicalUserInputEndToEndClaimed': False}, sort_keys=True))
    raise SystemExit(not result.result.wasSuccessful())
