"""Exercise Show Desktop and opening another window using isolated WebView state.

The unfixed phase reproduces the shell lowering a non-minimizable fullscreen
window. The fixed phase must stay minimized until an explicit restore, while
retaining exact fullscreen bounds and the normal border on exit.
"""
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'desktop'),str(ROOT/'backend')]


def run(directory):
    import webview
    from window_memory import fullscreen_frame,is_fullscreen
    user=ctypes.WinDLL('user32')
    for name,args in {
        'GetWindowLongW':[wintypes.HWND,ctypes.c_int],
        'GetForegroundWindow':[], 'SetForegroundWindow':[wintypes.HWND],
        'IsIconic':[wintypes.HWND], 'IsWindowVisible':[wintypes.HWND],
        'ShowWindow':[wintypes.HWND,ctypes.c_int],
    }.items():getattr(user,name).argtypes=args
    user.GetForegroundWindow.restype=wintypes.HWND
    previous=user.GetForegroundWindow()
    was_visible=[]
    callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    @callback
    def collect(handle,_):
        if user.IsWindowVisible(handle) and not user.IsIconic(handle):was_visible.append(handle)
        return True
    user.EnumWindows(collect,0)
    window=webview.create_window('ToBe isolated fullscreen desktop regression',
        html='<body>Isolated fullscreen desktop regression</body>',width=1100,height=740)
    result={}
    def verify():
        from System import Action
        from System.Windows.Forms import Form,FormWindowState,Screen
        other=[]
        def ui(fn):window.native.Invoke(Action(fn))
        def sample():
            form=window.native;handle=form.Handle.ToInt64();area=form.Bounds
            return {'minimized':bool(user.IsIconic(handle)),'fullscreen':is_fullscreen(window),
                'style':hex(user.GetWindowLongW(handle,-16)&0xffffffff),
                'foreground':user.GetForegroundWindow(),'handle':handle,
                'bounds':[area.X,area.Y,area.Width,area.Height]}
        try:
            assert window.events.loaded.wait(25),'WebView not ready'
            form=window.native;handle=form.Handle.ToInt64()
            for fixed in (False,True):
                window.toggle_fullscreen()
                if fixed:fullscreen_frame(window)
                before=[];ui(lambda:before.append(sample()))
                assert not before[0]['minimized'] and before[0]['fullscreen'],before
                def toggle_desktop():
                    user.keybd_event(0x5b,0,0,0)
                    user.keybd_event(0x44,0,0,0)
                    user.keybd_event(0x44,0,2,0)
                    user.keybd_event(0x5b,0,2,0)
                def desktop():
                    form.Activate();user.SetForegroundWindow(handle)
                ui(desktop);time.sleep(.2);toggle_desktop();time.sleep(.8)
                minimized=bool(user.IsIconic(handle))
                def open_other():
                    item=Form();item.Text='ToBe isolated other-window fixture'
                    item.Width=500;item.Height=340;item.Show();item.Activate();other.append(item)
                ui(open_other);time.sleep(.8)
                after=[];ui(lambda:after.append(sample()))
                if fixed:
                    assert minimized and after[0]['minimized'],after
                    assert user.GetForegroundWindow()!=handle,'Fullscreen window stole focus'
                else:
                    assert not minimized and not after[0]['minimized'],'Baseline did not reproduce'
                ui(lambda:other.pop().Close())
                toggle_desktop()
                time.sleep(.2)
                ui(lambda:(setattr(form,'WindowState',FormWindowState.Maximized),form.Activate()))
                time.sleep(.2)
                restored=[];ui(lambda:restored.append(sample()))
                assert restored[0]['bounds']==before[0]['bounds'],(before,restored)
                assert restored[0]['fullscreen'] and not restored[0]['minimized'],restored
                window.toggle_fullscreen();fullscreen_frame(window)
                normal=[];ui(lambda:normal.append(sample()))
                assert int(normal[0]['style'],16)&0x00c00000==0x00c00000,normal
                result['fixed' if fixed else 'baseline']={'before':before[0],'afterOtherWindow':after[0],
                    'minimizedByShowDesktop':minimized,'explicitRestore':restored[0],'normal':normal[0]}
            result['ok']=True
        except Exception as error:result.update(ok=False,error=repr(error))
        finally:
            for item in other:
                try:ui(item.Close)
                except Exception:pass
            window.destroy()
    webview.start(verify,gui='edgechromium',private_mode=True,storage_path=str(directory/'webview'))
    # Undo only minimization caused by this fixture; never activate a previously
    # minimized application or change the user's existing background choices.
    for handle in was_visible:
        if user.IsIconic(handle):user.ShowWindow(handle,4)  # SW_SHOWNOACTIVATE
    if previous:user.SetForegroundWindow(previous)
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result),flush=True)
    assert result.get('ok'),result


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
