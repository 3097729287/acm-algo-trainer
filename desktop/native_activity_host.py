"""Windows input host whose OS hook delegates never enter Python.

The managed type is loaded lazily once. A release can ship the verified DLL
and source/hash manifest; source-checkout fallback compiles once in memory.
There are no browser data, accounts, network calls or Python input delegates.
"""
import hashlib
import json
from pathlib import Path
import threading


SOURCE = r'''
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;

namespace ToBe.NativeInput {
 public sealed class Command {
  public readonly string Combo; public readonly long Serial,Sequence,Generation; public readonly uint Time;
  public Command(string combo,long serial,long sequence,long generation,uint time){Combo=combo;Serial=serial;Sequence=sequence;Generation=generation;Time=time;}
 }
 public sealed class Registration {
  public readonly HashSet<string> Keys; public readonly long Serial,Generation; public readonly bool Active;
  public Registration(string[] keys,long serial,bool active,long generation){Keys=new HashSet<string>(keys,StringComparer.Ordinal);Serial=serial;Active=active;Generation=generation;}
 }
 public sealed class InputState {
  public readonly long Revision;public readonly uint Time;
  public InputState(long revision,uint time){Revision=revision;Time=time;}
 }
 public sealed class ActivitySnapshot {
  public bool Available,Observed; public long Revision; public double AgeSeconds;
 }
 public sealed class Host : IDisposable {
  [StructLayout(LayoutKind.Sequential)] struct Point { public int X,Y; }
  [StructLayout(LayoutKind.Sequential)] struct Mouse {public Point Point;public uint Data,Flags,Time;public UIntPtr Extra;}
  [StructLayout(LayoutKind.Sequential)] struct Keyboard {public uint Key,Scan,Flags,Time;public UIntPtr Extra;}
  [StructLayout(LayoutKind.Sequential)] struct Rect {public int L,T,R,B;}
  [StructLayout(LayoutKind.Sequential)] struct Gui {public uint Size,Flags;public IntPtr Active,Focus,Capture,Menu,Move,Caret;public Rect Rect;}
  [StructLayout(LayoutKind.Sequential)] struct Message {public IntPtr Window;public uint Id;public UIntPtr W;public IntPtr L;public uint Time;public Point Point;public uint Private;}
  delegate IntPtr Hook(int code,UIntPtr message,IntPtr data);
  [DllImport("user32.dll",SetLastError=true)] static extern IntPtr SetWindowsHookExW(int kind,Hook callback,IntPtr module,uint thread);
  [DllImport("user32.dll")] static extern IntPtr CallNextHookEx(IntPtr hook,int code,UIntPtr message,IntPtr data);
  [DllImport("user32.dll")] static extern bool UnhookWindowsHookEx(IntPtr hook);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern IntPtr GetAncestor(IntPtr window,uint flags);
  [DllImport("user32.dll")] static extern bool IsWindow(IntPtr window);
  [DllImport("user32.dll")] static extern bool IsChild(IntPtr parent,IntPtr child);
  [DllImport("user32.dll")] static extern IntPtr WindowFromPoint(Point point);
  [DllImport("user32.dll")] static extern bool GetGUIThreadInfo(uint thread,ref Gui info);
  [DllImport("user32.dll")] static extern short GetAsyncKeyState(int key);
  [DllImport("user32.dll")] static extern int GetMessageW(out Message message,IntPtr window,uint low,uint high);
  [DllImport("user32.dll")] static extern bool PeekMessageW(out Message message,IntPtr window,uint low,uint high,uint remove);
  [DllImport("user32.dll")] static extern bool PostThreadMessageW(uint thread,uint message,UIntPtr w,IntPtr l);
  [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
  [DllImport("kernel32.dll")] static extern uint GetTickCount();
  [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern IntPtr GetModuleHandleW(string name);
  IntPtr window,main;Thread thread;Timer timer;Hook mouseCallback,keyCallback;
  volatile bool closed,available;uint threadId;int polling;
  long mousePoint,mouseTime,mouseRevision,consumedMouse,sequence;
  InputState activity=new InputState(0,0);
  Registration registration=new Registration(new string[0],0,false,0);
  readonly ManualResetEvent ready=new ManualResetEvent(false);
  readonly bool[] held=new bool[256];readonly Command[] commands=new Command[32];
  public string ErrorCode {get;private set;}
  public Host(long owner,long mainView){SetHandles(owner,mainView);}
  public void SetHandles(long owner,long mainView){Interlocked.Exchange(ref window,new IntPtr(owner));Interlocked.Exchange(ref main,new IntPtr(mainView));}
  IntPtr Window {get{return Interlocked.CompareExchange(ref window,IntPtr.Zero,IntPtr.Zero);}}
  bool Owned(IntPtr handle){IntPtr owner=Window;return owner!=IntPtr.Zero&&handle!=IntPtr.Zero&&IsWindow(owner)&&GetAncestor(handle,3)==owner;}
  public void Configure(string[] keys,long serial,bool active,long generation){
   Registration next=new Registration(keys,serial,active,generation);
   for(int i=0;i<4;i++){Registration before=Interlocked.CompareExchange(ref registration,null,null);if(generation<before.Generation)return;if(Object.ReferenceEquals(Interlocked.CompareExchange(ref registration,next,before),before))return;}
  }
  public void Start(){if(closed||thread!=null)return;thread=new Thread(Run);thread.IsBackground=true;thread.Name="tb-managed-input";thread.Start();}
  void Record(uint time){
   for(int i=0;i<4;i++){
    if(closed)return;
    InputState before=Interlocked.CompareExchange(ref activity,null,null);uint now=GetTickCount();
    if(before.Revision>0&&Age(now,time)>Age(now,before.Time))return;
    InputState next=new InputState(before.Revision+1,time);
    if(Object.ReferenceEquals(Interlocked.CompareExchange(ref activity,next,before),before))return;
   }
  }
  public bool WaitReady(int milliseconds){return ready.WaitOne(milliseconds);}
  public uint ClockNow(){return GetTickCount();}
  public ActivitySnapshot Snapshot(){InputState state=Interlocked.CompareExchange(ref activity,null,null);return new ActivitySnapshot{Available=available&&!closed,Observed=state.Revision!=0,Revision=state.Revision,AgeSeconds=state.Revision==0?0:Age(GetTickCount(),state.Time)};}
  public static double Age(uint now,uint then){return unchecked(now-then)/1000.0;}
  static bool Down(int key){return (GetAsyncKeyState(key)&0x8000)!=0;}
  IntPtr MouseHook(int code,UIntPtr message,IntPtr pointer){
   try{if(code==0&&!closed&&Owned(GetForegroundWindow())){
    Mouse value=(Mouse)Marshal.PtrToStructure(pointer,typeof(Mouse));
    if((value.Flags&3)==0){
     long point=unchecked(((long)(uint)value.Point.X<<32)|(uint)value.Point.Y);
     Interlocked.Increment(ref mouseRevision);
     Interlocked.Exchange(ref mousePoint,point);Interlocked.Exchange(ref mouseTime,value.Time);
     Interlocked.Increment(ref mouseRevision);
    }
   }}catch{ErrorCode="NATIVE_MOUSE_CALLBACK_FAILED";}
   return CallNextHookEx(IntPtr.Zero,code,message,pointer);
  }
  // Window hit-testing can wait for a window owner. It is never on the hook
  // thread: at most one timer callback is active and mouse motion coalesces.
  void PollMouse(object unused){
   if(closed||Interlocked.Exchange(ref polling,1)!=0)return;
   try{
    long current=Interlocked.Read(ref mouseRevision);if((current&1)!=0||current==Interlocked.Read(ref consumedMouse))return;
    long point=Interlocked.Read(ref mousePoint);uint time=(uint)Interlocked.Read(ref mouseTime);
    if(current!=Interlocked.Read(ref mouseRevision))return;
    Interlocked.Exchange(ref consumedMouse,current);
    if(!closed&&Owned(GetForegroundWindow())&&Owned(WindowFromPoint(new Point{X=(int)(point>>32),Y=unchecked((int)point)})))Record(time);
   }catch{ErrorCode="MOUSE_SAMPLE_FAILED";}finally{Interlocked.Exchange(ref polling,0);}
  }
  IntPtr KeyHook(int code,UIntPtr message,IntPtr pointer){
   try{if(code==0&&!closed){
    Keyboard value=(Keyboard)Marshal.PtrToStructure(pointer,typeof(Keyboard));
    if((value.Flags&0x12)==0){
     bool owned=Owned(GetForegroundWindow());if(owned)Record(value.Time);
     Registration config=Interlocked.CompareExchange(ref registration,null,null);
     bool up=(value.Flags&128)!=0,wasHeld=value.Key<256&&held[value.Key];
     if(up&&!wasHeld){}
     else if(owned&&config.Active){
      Gui gui=new Gui();gui.Size=(uint)Marshal.SizeOf(typeof(Gui));
      IntPtr root=Interlocked.CompareExchange(ref main,IntPtr.Zero,IntPtr.Zero);
      bool child=root!=IntPtr.Zero&&GetGUIThreadInfo(0,ref gui)&&gui.Focus!=IntPtr.Zero&&gui.Focus!=root&&!IsChild(root,gui.Focus);
      if(Capture(value.Key,value.Flags,child,Down(17),Down(18),Down(16),Down(91)||Down(92),value.Time))return new IntPtr(1);
     }
     else if(up&&wasHeld)held[value.Key]=false;
    }
   }}catch{ErrorCode="NATIVE_KEY_CALLBACK_FAILED";}
   return CallNextHookEx(IntPtr.Zero,code,message,pointer);
  }
  public static string Combination(uint key,bool control,bool alt,bool shift,bool meta){
   if(meta)return null;string value=null;
   if(key>=65&&key<=90)value=((char)key).ToString().ToLowerInvariant();
   else if(key>=48&&key<=57)value=(shift?")!@#$%^&*("[(int)key-48]:(char)key).ToString();
   else if(key>=112&&key<=135)value="f"+(key-111);
   else{
    switch(key){
     case 8:value="backspace";break;case 9:value="tab";break;case 13:value="enter";break;case 27:value="escape";break;case 32:value="space";break;
     case 33:value="pageup";break;case 34:value="pagedown";break;case 35:value="end";break;case 36:value="home";break;
     case 37:value="arrowleft";break;case 38:value="arrowup";break;case 39:value="arrowright";break;case 40:value="arrowdown";break;case 45:value="insert";break;case 46:value="delete";break;
     case 186:value=shift?":":";";break;case 187:value=shift?"+":"=";break;case 188:value=shift?"<":",";break;case 189:value=shift?"_":"-";break;
     case 190:value=shift?">":".";break;case 191:value=shift?"?":"/";break;case 192:value=shift?"~":"`";break;
     case 219:value=shift?"{":"[";break;case 220:value=shift?"|":"\\";break;case 221:value=shift?"}":"]";break;case 222:value=shift?"\"":"'";break;
    }
   }
   if(value==null)return null;
   if(!control&&!alt&&!(key>=112&&key<=135)&&key!=27)return null;
   bool explicitShift=shift&&(value.Length!=1||Char.IsLetter(value[0]));
   return (control?"ctrl+":"")+(alt?"alt+":"")+(explicitShift?"shift+":"")+value;
  }
  // The deterministic core is also testable without installing any OS hook.
  public bool Capture(uint key,uint flags,bool child,bool control,bool alt,bool shift,bool meta,uint time){
   if(closed||(flags&0x12)!=0||key>=256)return false;
   Registration config=Interlocked.CompareExchange(ref registration,null,null);bool up=(flags&128)!=0;
   if(held[key]){if(up)held[key]=false;return child&&config.Active;}
   if(up||!child||!config.Active)return false;
   string combo=Combination(key,control,alt,shift,meta);if(combo==null||!config.Keys.Contains(combo))return false;
   held[key]=true;long next=Interlocked.Read(ref sequence)+1;
   Interlocked.Exchange(ref commands[(int)((next-1)%32)],new Command(combo,config.Serial,next,config.Generation,time));
   Interlocked.Exchange(ref sequence,next);return true;
  }
  public Command[] Commands(){
   long last=Interlocked.Read(ref sequence);var result=new List<Command>(32);
   for(long n=Math.Max(1,last-31);n<=last;n++){Command value=Interlocked.CompareExchange(ref commands[(int)((n-1)%32)],null,null);if(value!=null&&value.Sequence==n)result.Add(value);}
   return result.ToArray();
  }
  void Run(){
   IntPtr mouse=IntPtr.Zero,key=IntPtr.Zero;
   try{
    threadId=GetCurrentThreadId();Message message;PeekMessageW(out message,IntPtr.Zero,0,0,0);
    mouseCallback=MouseHook;keyCallback=KeyHook;IntPtr module=GetModuleHandleW(null);
    mouse=SetWindowsHookExW(14,mouseCallback,module,0);key=SetWindowsHookExW(13,keyCallback,module,0);
    if(mouse==IntPtr.Zero||key==IntPtr.Zero)throw new InvalidOperationException();
    timer=new Timer(PollMouse,null,50,50);available=true;ready.Set();
    while(!closed&&GetMessageW(out message,IntPtr.Zero,0,0)>0){}
   }catch{ErrorCode="NATIVE_HOOK_SETUP_FAILED";}
   finally{available=false;if(timer!=null)timer.Dispose();if(mouse!=IntPtr.Zero)UnhookWindowsHookEx(mouse);if(key!=IntPtr.Zero)UnhookWindowsHookEx(key);ready.Set();}
  }
  public void Dispose(){closed=true;available=false;ready.Set();if(timer!=null)timer.Dispose();if(threadId!=0)PostThreadMessageW(threadId,0x12,UIntPtr.Zero,IntPtr.Zero);if(thread!=null&&Thread.CurrentThread!=thread)thread.Join(1000);}
 }
}
'''

SOURCE_SHA256 = hashlib.sha256(SOURCE.encode('utf-8')).hexdigest()
_type = None
_type_lock = threading.Lock()


def _provider():
    import clr
    clr.AddReference('System')
    clr.AddReference('Microsoft.CSharp')
    from Microsoft.CSharp import CSharpCodeProvider
    from System.CodeDom.Compiler import CompilerParameters
    return CSharpCodeProvider, CompilerParameters


def build(destination):
    """Optional packaging hook: write the public DLL and hash manifest once."""
    destination = Path(destination)
    if destination.exists() or destination.with_suffix('.json').exists():
        raise RuntimeError('NATIVE_INPUT_OUTPUT_EXISTS')
    provider_type, parameter_type = _provider()
    provider, parameters = provider_type(), parameter_type()
    parameters.GenerateExecutable = False
    parameters.GenerateInMemory = False
    parameters.OutputAssembly = str(destination)
    parameters.ReferencedAssemblies.Add('System.dll')
    parameters.ReferencedAssemblies.Add('System.Core.dll')
    result = provider.CompileAssemblyFromSource(parameters, SOURCE)
    if result.Errors.HasErrors:
        raise RuntimeError('NATIVE_INPUT_COMPILE_FAILED')
    metadata = {'schema': 1, 'sourceSha256': SOURCE_SHA256,
                'assemblySha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
    with destination.with_suffix('.json').open('x', encoding='utf-8') as stream:
        json.dump(metadata, stream, sort_keys=True)
    return metadata


def managed_type():
    global _type
    with _type_lock:
        if _type is not None:
            return _type
        import clr
        # Packaging can supply these two files beside the frozen helper's
        # resource directory. Cache/profile locations are never DLL sources.
        from paths import resource
        assembly = resource('native-input-host.dll')
        manifest = assembly.with_suffix('.json')
        if assembly.exists() != manifest.exists():
            raise RuntimeError('NATIVE_INPUT_ASSEMBLY_INCOMPLETE')
        if assembly.is_file() and manifest.is_file():
            metadata = json.loads(manifest.read_text('utf-8'))
            if metadata != {'schema': 1, 'sourceSha256': SOURCE_SHA256,
                            'assemblySha256': hashlib.sha256(assembly.read_bytes()).hexdigest()}:
                raise RuntimeError('NATIVE_INPUT_ASSEMBLY_HASH_MISMATCH')
            clr.AddReference(str(assembly.resolve()))
        else:
            provider_type, parameter_type = _provider()
            provider, parameters = provider_type(), parameter_type()
            parameters.GenerateExecutable = False
            parameters.GenerateInMemory = True
            parameters.ReferencedAssemblies.Add('System.dll')
            parameters.ReferencedAssemblies.Add('System.Core.dll')
            result = provider.CompileAssemblyFromSource(parameters, SOURCE)
            if result.Errors.HasErrors:
                raise RuntimeError('NATIVE_INPUT_COMPILE_FAILED')
            clr.AddReference(result.CompiledAssembly.FullName)
            # In-memory compilation is process-cached and runs before hooks
            # exist. No hook callback can cause compilation or load a module.
        from ToBe.NativeInput import Host
        _type = Host
        return _type
