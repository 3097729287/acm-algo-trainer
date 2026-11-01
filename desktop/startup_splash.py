"""Small native loading window, available before WebView and database startup."""
import ctypes
from ctypes import wintypes as w
import logging
import os
import threading


class StartupSplash:
    def __init__(self,visible=True):
        self.ready=threading.Event();self.closed=threading.Event();self.hwnd=None
        self.visible=visible;self._post_close=None

    def show(self):
        if os.name!='nt':return
        threading.Thread(target=self._run,name='tb-startup-window',daemon=True).start()
        self.ready.wait(.1)

    def close(self):
        self.closed.set()
        if self.hwnd and self._post_close:self._post_close(self.hwnd,0x0010,0,0)

    def _run(self):
        try:self._window_loop()
        except Exception:logging.getLogger('tb.desktop').warning('Native loading window unavailable',exc_info=True)
        finally:self.hwnd=None;self.ready.set()

    def _window_loop(self):
        user=ctypes.WinDLL('user32',use_last_error=True);gdi=ctypes.WinDLL('gdi32',use_last_error=True);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        callback=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
        class WindowClass(ctypes.Structure):
            _fields_=[('style',w.UINT),('proc',callback),('classExtra',ctypes.c_int),('windowExtra',ctypes.c_int),('instance',w.HINSTANCE),('icon',w.HICON),('cursor',w.HANDLE),('background',w.HBRUSH),('menu',w.LPCWSTR),('name',w.LPCWSTR)]
        class Paint(ctypes.Structure):
            _fields_=[('dc',w.HDC),('erase',w.BOOL),('rect',w.RECT),('restore',w.BOOL),('update',w.BOOL),('reserved',w.BYTE*32)]
        kernel.GetModuleHandleW.argtypes=[w.LPCWSTR];kernel.GetModuleHandleW.restype=w.HINSTANCE
        user.DefWindowProcW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];user.DefWindowProcW.restype=ctypes.c_ssize_t
        user.RegisterClassW.argtypes=[ctypes.POINTER(WindowClass)];user.RegisterClassW.restype=w.ATOM
        user.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,w.HWND,w.HMENU,w.HINSTANCE,w.LPVOID];user.CreateWindowExW.restype=w.HWND
        user.BeginPaint.argtypes=[w.HWND,ctypes.POINTER(Paint)];user.BeginPaint.restype=w.HDC
        user.EndPaint.argtypes=[w.HWND,ctypes.POINTER(Paint)]
        user.FillRect.argtypes=[w.HDC,ctypes.POINTER(w.RECT),w.HBRUSH]
        user.DrawTextW.argtypes=[w.HDC,w.LPCWSTR,ctypes.c_int,ctypes.POINTER(w.RECT),w.UINT]
        user.DestroyWindow.argtypes=[w.HWND]
        user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        self._post_close=user.PostMessageW
        user.ShowWindow.argtypes=[w.HWND,ctypes.c_int];user.UpdateWindow.argtypes=[w.HWND]
        user.GetMessageW.argtypes=[ctypes.POINTER(w.MSG),w.HWND,w.UINT,w.UINT]
        user.TranslateMessage.argtypes=[ctypes.POINTER(w.MSG)]
        user.DispatchMessageW.argtypes=[ctypes.POINTER(w.MSG)];user.DispatchMessageW.restype=ctypes.c_ssize_t
        user.UnregisterClassW.argtypes=[w.LPCWSTR,w.HINSTANCE]
        gdi.CreateSolidBrush.argtypes=[w.COLORREF];gdi.CreateSolidBrush.restype=w.HBRUSH
        gdi.SelectObject.argtypes=[w.HDC,w.HANDLE];gdi.SelectObject.restype=w.HANDLE
        gdi.DeleteObject.argtypes=[w.HANDLE]
        gdi.SetTextColor.argtypes=[w.HDC,w.COLORREF];gdi.SetBkMode.argtypes=[w.HDC,ctypes.c_int]
        gdi.CreateFontW.argtypes=[ctypes.c_int]*5+[w.DWORD]*8+[w.LPCWSTR];gdi.CreateFontW.restype=w.HFONT
        dpi=user.GetDpiForSystem() if hasattr(user,'GetDpiForSystem') else 96
        scale=dpi/96;width,height=int(360*scale),int(158*scale)
        color=lambda r,g,b:r|(g<<8)|(b<<16)
        background=gdi.CreateSolidBrush(color(16,17,22));accent=gdi.CreateSolidBrush(color(106,205,180))
        def draw_text(dc,text,size,weight,top,bottom,ink):
            font=gdi.CreateFontW(-int(size*scale),0,0,0,weight,0,0,0,1,0,0,5,0,'Segoe UI')
            previous=gdi.SelectObject(dc,font);gdi.SetTextColor(dc,ink)
            rect=w.RECT(0,int(top*scale),width,int(bottom*scale))
            user.DrawTextW(dc,text,-1,ctypes.byref(rect),0x0001|0x0004|0x0020)
            gdi.SelectObject(dc,previous);gdi.DeleteObject(font)
        @callback
        def procedure(hwnd,message,wp,lp):
            if message==0x000F:
                paint=Paint();dc=user.BeginPaint(hwnd,ctypes.byref(paint));gdi.SetBkMode(dc,1)
                rect=w.RECT(0,0,width,height);user.FillRect(dc,ctypes.byref(rect),background)
                draw_text(dc,'ToBe',30,600,25,76,color(233,239,245))
                draw_text(dc,'正在打开 ToBe…',13,400,81,109,color(167,177,194))
                bar=w.RECT(int(138*scale),int(129*scale),int(222*scale),int(132*scale));user.FillRect(dc,ctypes.byref(bar),accent)
                user.EndPaint(hwnd,ctypes.byref(paint));return 0
            if message==0x0002:user.PostQuitMessage(0);return 0
            return user.DefWindowProcW(hwnd,message,wp,lp)
        self._procedure=procedure
        instance=kernel.GetModuleHandleW(None);name='ToBe.Startup.'+str(os.getpid())
        klass=WindowClass(0,procedure,0,0,instance,None,None,background,None,name)
        if not user.RegisterClassW(ctypes.byref(klass)):raise ctypes.WinError(ctypes.get_last_error())
        try:
            x=(user.GetSystemMetrics(0)-width)//2;y=(user.GetSystemMetrics(1)-height)//2
            self.hwnd=user.CreateWindowExW(0x00000080,name,'ToBe',0x80000000,x,y,width,height,None,None,instance,None)
            if not self.hwnd:raise ctypes.WinError(ctypes.get_last_error())
            if self.closed.is_set():user.PostMessageW(self.hwnd,0x0010,0,0)
            else:
                if self.visible:user.ShowWindow(self.hwnd,4)
                user.UpdateWindow(self.hwnd)
            self.ready.set();message=w.MSG()
            while user.GetMessageW(ctypes.byref(message),None,0,0)>0:
                user.TranslateMessage(ctypes.byref(message));user.DispatchMessageW(ctypes.byref(message))
        finally:
            user.UnregisterClassW(name,instance);gdi.DeleteObject(accent);gdi.DeleteObject(background)
