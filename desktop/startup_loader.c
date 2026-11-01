/* Native shortcut entry: paint before loading Python, WebView or SQLite.
 * The child remains the normal application, with its original identity and
 * single-instance/migration rules. No network, account or storage work here. */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <wchar.h>

static PROCESS_INFORMATION child;
static HBRUSH background, accent;
static HFONT title_font, body_font;
static int width, height, scale;
static HWND splash;

static BOOL CALLBACK main_visible(HWND window, LPARAM data) {
    DWORD pid=0; GetWindowThreadProcessId(window,&pid);
    if (pid!=child.dwProcessId || !IsWindowVisible(window)) return TRUE;
    wchar_t name[100];GetClassNameW(window,name,100);
    if (wcsncmp(name,L"WindowsForms10.Window.",22)==0 || wcscmp(name,L"#32770")==0) {
        *(BOOL*)data=TRUE;return FALSE;
    }
    return TRUE;
}
static LRESULT CALLBACK procedure(HWND window,UINT msg,WPARAM wp,LPARAM lp) {
    if (msg==WM_PAINT) {
        PAINTSTRUCT paint;HDC dc=BeginPaint(window,&paint);
        RECT all={0,0,width,height};FillRect(dc,&all,background);SetBkMode(dc,TRANSPARENT);
        HGDIOBJ old=SelectObject(dc,title_font);SetTextColor(dc,RGB(233,239,245));
        RECT text={0,MulDiv(25,scale,96),width,MulDiv(76,scale,96)};
        DrawTextW(dc,L"ToBe",-1,&text,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        SelectObject(dc,body_font);SetTextColor(dc,RGB(167,177,194));
        text.top=MulDiv(81,scale,96);text.bottom=MulDiv(109,scale,96);
        DrawTextW(dc,L"正在打开 ToBe…",-1,&text,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        RECT bar={MulDiv(138,scale,96),MulDiv(129,scale,96),MulDiv(222,scale,96),MulDiv(132,scale,96)};
        FillRect(dc,&bar,accent);SelectObject(dc,old);EndPaint(window,&paint);return 0;
    }
    if(msg==WM_TIMER) {
        BOOL visible=FALSE;EnumWindows(main_visible,(LPARAM)&visible);
        if(visible||WaitForSingleObject(child.hProcess,0)==WAIT_OBJECT_0)DestroyWindow(window);
        return 0;
    }
    if(msg==WM_DESTROY){splash=NULL;PostQuitMessage(0);return 0;}
    return DefWindowProcW(window,msg,wp,lp);
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE previous,LPWSTR arguments,int display) {
    (void)previous;(void)display;
    wchar_t directory[32768], executable[32768], command[32768];
    DWORD length=GetModuleFileNameW(NULL,directory,32768);
    if(!length||length>=32767)return 1;
    wchar_t *last=wcsrchr(directory,L'\\');if(!last)return 1;*last=0;
    if(swprintf(executable,32768,L"%ls\\ToBe.exe",directory)<0)return 1;
    if(GetFileAttributesW(executable)==INVALID_FILE_ATTRIBUTES)
        if(swprintf(executable,32768,L"%ls\\ToBe管理员版.exe",directory)<0)return 1;
    if(swprintf(command,32768,L"\"%ls\" %ls",executable,arguments)<0)return 1;
    if(!*arguments) {
        SetProcessDPIAware();scale=(int)GetDpiForSystem();
        width=MulDiv(360,scale,96);height=MulDiv(158,scale,96);
        background=CreateSolidBrush(RGB(16,17,22));accent=CreateSolidBrush(RGB(106,205,180));
        title_font=CreateFontW(-MulDiv(30,scale,96),0,0,0,600,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        body_font=CreateFontW(-MulDiv(13,scale,96),0,0,0,400,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        WNDCLASSW klass={0};klass.lpfnWndProc=procedure;klass.hInstance=instance;
        klass.hbrBackground=background;klass.lpszClassName=L"ToBe.NativeLoading";
        if(RegisterClassW(&klass)) {
            splash=CreateWindowExW(WS_EX_TOOLWINDOW,klass.lpszClassName,L"ToBe",WS_POPUP,
                (GetSystemMetrics(SM_CXSCREEN)-width)/2,(GetSystemMetrics(SM_CYSCREEN)-height)/2,
                width,height,NULL,NULL,instance,NULL);
            if(splash){ShowWindow(splash,SW_SHOWNOACTIVATE);UpdateWindow(splash);}
        }
        if(splash)SetEnvironmentVariableW(L"TB_NATIVE_LOADING",L"1");
    }
    STARTUPINFOW startup={0};startup.cb=sizeof(startup);
    BOOL started=CreateProcessW(executable,command,NULL,NULL,FALSE,0,NULL,directory,&startup,&child);
    SetEnvironmentVariableW(L"TB_NATIVE_LOADING",NULL);
    if(!started) {
        if(splash)DestroyWindow(splash);
        MessageBoxW(NULL,L"ToBe 未能启动，请重新打开程序。",L"ToBe",MB_OK|MB_ICONERROR);return 1;
    }
    CloseHandle(child.hThread);
    if(splash){SetTimer(splash,1,50,NULL);MSG message;
        while(GetMessageW(&message,NULL,0,0)>0){TranslateMessage(&message);DispatchMessageW(&message);}}
    if(title_font)DeleteObject(title_font);
    if(body_font)DeleteObject(body_font);
    if(background)DeleteObject(background);
    if(accent)DeleteObject(accent);
    /* Waiting preserves normal process lifetime for shortcuts and updaters. */
    WaitForSingleObject(child.hProcess,INFINITE);DWORD exit_code=0;
    GetExitCodeProcess(child.hProcess,&exit_code);CloseHandle(child.hProcess);return (int)exit_code;
}
