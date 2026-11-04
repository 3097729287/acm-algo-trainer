"""Remember normal window bounds and maximization in the private SQLite state."""
from persistence import load_document, save_document


def is_fullscreen(window):
    """pywebview's Windows host owns the current fullscreen state."""
    native = getattr(window, 'native', None)
    return bool(getattr(native, 'is_fullscreen', getattr(window, 'fullscreen', False)))


def fullscreen_frame(window):
    """Remove the shadow's client-area margins as well as rounded corners.

    pywebview enables a one-pixel DWM glass frame when creating the normal
    window. Changing FormBorderStyle alone leaves that frame around the view.
    Run after each fullscreen transition, on the owning WinForms UI thread.
    """
    import ctypes
    from ctypes import wintypes
    from System import Action
    form=window.native
    def apply():
        class Margins(ctypes.Structure):
            _fields_=[(name,ctypes.c_int) for name in ('left','right','top','bottom')]
        dwm=ctypes.WinDLL('dwmapi');handle=wintypes.HWND(form.Handle.ToInt64())
        dwm.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
        dwm.DwmExtendFrameIntoClientArea.argtypes=[wintypes.HWND,ctypes.POINTER(Margins)]
        full=is_fullscreen(window);shadow=bool(getattr(window,'shadow',True))
        if full:
            # FormBorderStyle.None removes WS_MINIMIZEBOX. Win+D then only
            # lowers this window, and opening Explorer brings it back behind
            # Explorer. Retain native minimization in fullscreen so the shell
            # really minimizes it until the user chooses to restore it.
            user=ctypes.WinDLL('user32',use_last_error=True)
            user.GetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int]
            user.GetWindowLongW.restype=ctypes.c_long
            user.SetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_long]
            user.SetWindowLongW.restype=ctypes.c_long
            user.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
            style=user.GetWindowLongW(handle,-16)
            minimize_style=0x00020000|0x00080000  # WS_MINIMIZEBOX | WS_SYSMENU
            if style&minimize_style!=minimize_style:
                user.SetWindowLongW(handle,-16,style|minimize_style)
                # Refresh styles without moving, showing, activating or
                # changing the stacking order of this window.
                user.SetWindowPos(handle,None,0,0,0,0,0x0001|0x0002|0x0004|0x0010|0x0020)
        # pywebview forces DWMNCRP_ENABLED while enabling its normal-window
        # shadow. That draws a frame even after FormBorderStyle becomes None.
        # Let the borderless fullscreen style control nonclient rendering;
        # restore the normal shadow policy when leaving fullscreen.
        for attribute,value in [(2,0 if full or not shadow else 2),(33,1 if full else 0),(34,0xfffffffe if full else 0xffffffff)]:
            number=ctypes.c_uint32(value);dwm.DwmSetWindowAttribute(handle,attribute,ctypes.byref(number),4)
        margin=0 if full or not shadow else 1
        dwm.DwmExtendFrameIntoClientArea(handle,ctypes.byref(Margins(margin,margin,margin,margin)))
    if form.InvokeRequired:form.Invoke(Action(apply))
    else:apply()


def fit_bounds(saved, screens):
    screens=list(screens) or [(0, 0, 1480, 920)]
    try:
        x,y,w,h=(int(saved[key]) for key in ('x','y','width','height'))
        if w<=0 or h<=0:raise ValueError()
    except (KeyError,ValueError,TypeError,OverflowError):
        sx,sy,sw,sh=screens[0];w,h=min(1480,sw),min(920,sh)
        x,y=sx+(sw-w)//2,sy+(sh-h)//2
    def overlap(screen):
        sx,sy,sw,sh=screen
        return max(0,min(x+w,sx+sw)-max(x,sx))*max(0,min(y+h,sy+sh)-max(y,sy))
    sx,sy,sw,sh=max(screens,key=overlap)
    w,h=min(max(1050,w),sw),min(max(700,h),sh)
    return {'x':max(sx,min(x,sx+sw-w)),'y':max(sy,min(y,sy+sh-h)),
            'width':w,'height':h,'maximized':saved.get('maximized') is True}


def remembered(path):
    import ctypes
    from ctypes import wintypes
    class MonitorInfo(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('monitor',wintypes.RECT),('work',wintypes.RECT),('flags',wintypes.DWORD)]
    screens=[];user=ctypes.WinDLL('user32')
    callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HANDLE,wintypes.HDC,ctypes.POINTER(wintypes.RECT),wintypes.LPARAM)
    user.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.POINTER(MonitorInfo)]
    @callback
    def observe(handle,_dc,_rectangle,_context):
        info=MonitorInfo();info.size=ctypes.sizeof(info)
        if user.GetMonitorInfoW(handle,ctypes.byref(info)):
            area=info.work;item=(area.left,area.top,area.right-area.left,area.bottom-area.top)
            if info.flags&1:screens.insert(0,item)
            else:screens.append(item)
        return True
    user.EnumDisplayMonitors.argtypes=[wintypes.HDC,ctypes.c_void_p,callback,wintypes.LPARAM]
    user.EnumDisplayMonitors(None,None,observe,0)
    saved=load_document(path,{})
    return fit_bounds(saved if isinstance(saved,dict) else {},screens)


def bind(window,path):
    def restore():
        # pywebview interprets create_window coordinates as logical pixels and
        # scales them. Saved WinForms bounds are physical pixels. Restore once
        # on the UI thread, after DPI initialization and before the form shows.
        from System.Drawing import Rectangle,Size
        from System.Windows.Forms import FormStartPosition,FormWindowState,Screen
        saved=load_document(path,{})
        if not isinstance(saved,dict) or not all(key in saved for key in ('x','y','width','height')):return
        bounds=remembered(path);form=window.native
        rectangle=Rectangle(bounds['x'],bounds['y'],bounds['width'],bounds['height'])
        area=Screen.FromRectangle(rectangle).WorkingArea
        form.MinimumSize=Size(min(form.MinimumSize.Width,area.Width),min(form.MinimumSize.Height,area.Height))
        form.WindowState=FormWindowState.Normal
        form.StartPosition=FormStartPosition.Manual
        form.Bounds=rectangle
        if bounds['maximized']:form.WindowState=FormWindowState.Maximized
    def closing():
        from System.Windows.Forms import FormWindowState
        form=window.native
        if form is None or form.IsDisposed:return
        # 全屏（pywebview toggle_fullscreen）时先退出全屏，避免把全屏 Bounds 存成正常尺寸。
        if is_fullscreen(window):
            try:window.toggle_fullscreen()
            except Exception:pass
        state=form.WindowState
        bounds=form.Bounds if state==FormWindowState.Normal else form.RestoreBounds
        save_document(path,{'x':bounds.X,'y':bounds.Y,'width':bounds.Width,'height':bounds.Height,
                            'maximized':state==FormWindowState.Maximized})
    window.events.before_show+=restore
    window.events.closing+=closing
