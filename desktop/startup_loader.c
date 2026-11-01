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
static HBRUSH background, accent, panel, muted;
static HFONT title_font, body_font;
static int width, height, scale;
static HWND splash;
static int px(int value){return MulDiv(value,scale,96);}
static int smaller(int left,int right){return left<right?left:right;}

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
        RECT all;GetClientRect(window,&all);width=all.right;height=all.bottom;
        FillRect(dc,&all,background);SetBkMode(dc,TRANSPARENT);
        int sidebar=px(140),top=px(72);
        HGDIOBJ old=SelectObject(dc,title_font);SetTextColor(dc,RGB(233,239,245));
        RECT text={px(20),px(17),sidebar-px(8),px(56)};
        DrawTextW(dc,L"ToBe",-1,&text,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
        RECT line={sidebar,0,sidebar+1,height};FillRect(dc,&line,panel);
        line.left=sidebar;line.top=top;line.right=width;line.bottom=top+1;FillRect(dc,&line,panel);
        RECT search={sidebar+px(18),px(17),sidebar+px(448),px(55)};
        FillRect(dc,&search,panel);
        SelectObject(dc,body_font);SetTextColor(dc,RGB(167,177,194));
        const wchar_t *labels[]={L"我的训练",L"题库",L"题单",L"比赛",L"模拟赛",L"成长",L"提交记录",L"从零讲"};
        for(int index=0;index<8;index++){
            int y=px(80+index*44);
            RECT icon={px(21),y+px(12),px(33),y+px(24)};FrameRect(dc,&icon,muted);
            text.left=px(43);text.right=sidebar-px(8);text.top=y;text.bottom=y+px(38);
            DrawTextW(dc,labels[index],-1,&text,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
        }
        text.left=px(21);text.top=height-px(48);text.right=sidebar-px(8);text.bottom=height-px(10);
        DrawTextW(dc,L"设置",-1,&text,DT_LEFT|DT_VCENTER|DT_SINGLELINE);
        int center_x=(sidebar+width)/2,center_y=(top+height)/2;
        text.left=sidebar+px(24);text.right=width-px(24);text.top=center_y-px(40);text.bottom=center_y-px(10);
        SetTextColor(dc,RGB(233,239,245));DrawTextW(dc,L"正在加载 ToBe",-1,&text,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        text.top=center_y-px(8);text.bottom=center_y+px(18);SetTextColor(dc,RGB(167,177,194));
        DrawTextW(dc,L"正在准备训练工作台…",-1,&text,DT_CENTER|DT_VCENTER|DT_SINGLELINE);
        RECT bar={center_x-px(76),center_y+px(44),center_x+px(76),center_y+px(47)};
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
        RECT work;SystemParametersInfoW(SPI_GETWORKAREA,0,&work,0);
        width=smaller(px(1480),work.right-work.left);height=smaller(px(920),work.bottom-work.top);
        background=CreateSolidBrush(RGB(16,17,22));accent=CreateSolidBrush(RGB(106,205,180));
        panel=CreateSolidBrush(RGB(32,36,44));muted=CreateSolidBrush(RGB(125,136,151));
        title_font=CreateFontW(-px(19),0,0,0,600,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Segoe UI");
        body_font=CreateFontW(-px(14),0,0,0,400,0,0,0,DEFAULT_CHARSET,0,0,CLEARTYPE_QUALITY,0,L"Microsoft YaHei UI");
        WNDCLASSW klass={0};klass.lpfnWndProc=procedure;klass.hInstance=instance;
        klass.hbrBackground=background;klass.lpszClassName=L"ToBe.NativeLoading";
        if(RegisterClassW(&klass)) {
            splash=CreateWindowExW(WS_EX_TOOLWINDOW,klass.lpszClassName,L"ToBe",WS_POPUP,
                work.left+(work.right-work.left-width)/2,work.top+(work.bottom-work.top-height)/2,
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
    if(panel)DeleteObject(panel);
    if(muted)DeleteObject(muted);
    /* Waiting preserves normal process lifetime for shortcuts and updaters. */
    WaitForSingleObject(child.hProcess,INFINITE);DWORD exit_code=0;
    GetExitCodeProcess(child.hProcess,&exit_code);CloseHandle(child.hProcess);return (int)exit_code;
}
