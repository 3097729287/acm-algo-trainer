#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <shellapi.h>
#include <commctrl.h>
#include <objbase.h>
#include <stdio.h>
#include <stdlib.h>

static WCHAR work[MAX_PATH], statusPath[MAX_PATH];
static HWND label, bar;
static HBRUSH background;

static BOOL extract(WORD id, const WCHAR *name) {
    HRSRC r=FindResourceW(NULL,MAKEINTRESOURCEW(id),RT_RCDATA);
    if(!r)return FALSE;
    DWORD size=SizeofResource(NULL,r), written=0;
    const void *data=LockResource(LoadResource(NULL,r));
    WCHAR path[MAX_PATH];swprintf(path,MAX_PATH,L"%ls\\%ls",work,name);
    HANDLE f=CreateFileW(path,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);
    if(f==INVALID_HANDLE_VALUE)return FALSE;
    BOOL ok=WriteFile(f,data,size,&written,NULL)&&written==size&&FlushFileBuffers(f);
    CloseHandle(f);return ok;
}

static LRESULT CALLBACK window_proc(HWND w,UINT m,WPARAM a,LPARAM b) {
    if(m==WM_CTLCOLORSTATIC){SetTextColor((HDC)a,RGB(230,233,239));SetBkColor((HDC)a,RGB(23,25,32));return (LRESULT)background;}
    if(m==WM_CLOSE)return 0;
    return DefWindowProcW(w,m,a,b);
}

static void progress(void) {
    HANDLE f=CreateFileW(statusPath,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(f==INVALID_HANDLE_VALUE)return;
    char text[128]={0};DWORD got=0;ReadFile(f,text,127,&got,NULL);CloseHandle(f);
    int stage=0;unsigned long long done=0,total=0;
    if(sscanf(text,"%d|%llu|%llu",&stage,&done,&total)!=3)return;
    WCHAR message[160];
    if(stage==1&&total){
        swprintf(message,160,L"正在下载更新  %.1f%%  (%.1f / %.1f MB)",100.0*done/total,done/1048576.0,total/1048576.0);
        SendMessageW(bar,PBM_SETPOS,(WPARAM)(10000.0*done/total),0);
    }else if(stage==2)lstrcpyW(message,L"正在校验并重建程序，保留个人记录…");
    else if(stage==3)lstrcpyW(message,L"正在准备重新打开 ToBe…");
    else lstrcpyW(message,L"正在检查当前安装…");
    SetWindowTextW(label,message);
}

int WINAPI wWinMain(HINSTANCE instance,HINSTANCE previous,PWSTR command,int show) {
    int count=0;LPWSTR *args=CommandLineToArgvW(GetCommandLineW(),&count);
    WCHAR app[32768]=L"";BOOL silent=FALSE,noRestart=FALSE;
    for(int i=1;i<count;i++){
        if(!_wcsnicmp(args[i],L"/DIR=",5)){
            if(wcslen(args[i]+5)>30000||wcschr(args[i]+5,L'"')||wcschr(args[i]+5,L'\n')){LocalFree(args);return 2;}
            lstrcpyW(app,args[i]+5);
        }
        /* Automatic callers use /SILENT to suppress questions. Keep the real
           progress visible; only /VERYSILENT explicitly hides all windows. */
        if(!_wcsicmp(args[i],L"/VERYSILENT"))silent=TRUE;
        if(!_wcsicmp(args[i],L"/NORESTART"))noRestart=TRUE;
    }
    LocalFree(args);
    WCHAR temporary[MAX_PATH];if(!GetTempPathW(MAX_PATH,temporary))return 2;
    GUID id;if(FAILED(CoCreateGuid(&id)))return 2;
    WCHAR key[40];StringFromGUID2(&id,key,40);
    if(swprintf(work,MAX_PATH,L"%lsToBeUpdateBridge-%ls",temporary,key)<0||!CreateDirectoryW(work,NULL))return 2;
    if(!extract(101,L"compact-helper.pyz")||!extract(102,L"apply.ps1")||!extract(103,L"release.json"))return 2;
    swprintf(statusPath,MAX_PATH,L"%ls\\progress.txt",work);
    WCHAR windows[MAX_PATH],exe[MAX_PATH];if(!GetSystemDirectoryW(windows,MAX_PATH))return 2;
    swprintf(exe,MAX_PATH,L"%ls\\WindowsPowerShell\\v1.0\\powershell.exe",windows);
    WCHAR line[32768];
    if(swprintf(line,32768,L"\"%ls\" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File \"%ls\\apply.ps1\" -WorkDir \"%ls\" -AppDir \"%ls\"%ls",exe,work,work,app,(!silent&&!noRestart)?L" -Restart":L"")<0)return 2;
    STARTUPINFOW startup={0};PROCESS_INFORMATION process={0};startup.cb=sizeof(startup);startup.dwFlags=STARTF_USESHOWWINDOW;startup.wShowWindow=SW_HIDE;
    if(!CreateProcessW(exe,line,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,work,&startup,&process))return 2;
    CloseHandle(process.hThread);
    HWND window=NULL;
    if(!silent){
        INITCOMMONCONTROLSEX controls={sizeof(controls),ICC_PROGRESS_CLASS};InitCommonControlsEx(&controls);
        background=CreateSolidBrush(RGB(23,25,32));
        WNDCLASSW cls={0};cls.lpfnWndProc=window_proc;cls.hInstance=instance;cls.hbrBackground=background;cls.lpszClassName=L"ToBeCompactUpdate";cls.hIcon=LoadIconW(instance,MAKEINTRESOURCEW(1));cls.hCursor=LoadCursorW(NULL,IDC_ARROW);RegisterClassW(&cls);
        window=CreateWindowExW(0,cls.lpszClassName,L"ToBe 更新",WS_CAPTION|WS_SYSMENU,CW_USEDEFAULT,CW_USEDEFAULT,480,142,NULL,NULL,instance,NULL);
        EnableMenuItem(GetSystemMenu(window,FALSE),SC_CLOSE,MF_BYCOMMAND|MF_GRAYED);
        label=CreateWindowExW(0,L"STATIC",L"正在检查当前安装…",WS_CHILD|WS_VISIBLE,20,20,430,24,window,NULL,instance,NULL);
        bar=CreateWindowExW(0,PROGRESS_CLASSW,L"",WS_CHILD|WS_VISIBLE,20,63,430,16,window,NULL,instance,NULL);
        SendMessageW(bar,PBM_SETRANGE32,0,10000);ShowWindow(window,SW_SHOW);
        /* The old updater launches setup with STARTUPINFO=SW_HIDE. Its startup
           state can override the first ShowWindow call. Show progress without
           activation if that happened; /VERYSILENT never creates this window. */
        if(!IsWindowVisible(window))ShowWindow(window,SW_SHOWNOACTIVATE);
        UpdateWindow(window);
    }
    DWORD result=2;
    for(;;){
        DWORD waited=MsgWaitForMultipleObjects(1,&process.hProcess,FALSE,200,QS_ALLINPUT);
        if(waited==WAIT_OBJECT_0)break;
        if(waited==WAIT_FAILED)break;
        MSG message;while(PeekMessageW(&message,NULL,0,0,PM_REMOVE)){TranslateMessage(&message);DispatchMessageW(&message);}
        if(window)progress();
    }
    GetExitCodeProcess(process.hProcess,&result);CloseHandle(process.hProcess);
    if(window)DestroyWindow(window);
    if(background)DeleteObject(background);
    if(result!=0&&!silent){
        WCHAR message[800];swprintf(message,800,L"更新未完成，原记录和恢复文件已保留。请先关闭 ToBe 后重试。\n\n诊断文件：%ls\\result.json",work);
        MessageBoxW(NULL,message,L"ToBe 更新",MB_OK|MB_ICONERROR);
    }
    return (int)result;
}
