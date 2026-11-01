import {Check,Code2} from 'lucide-react';
import CodeEditor from '@/components/CodeEditor.jsx';
import {EDITOR_THEMES,editorTheme,editorThemeStyle} from '@/lib/editorThemes.js';
import './EditorThemeSettings.css';

const EXAMPLE=`#include <bits/stdc++.h>
using namespace std;

// 前缀和与二分：找到第一个满足条件的位置。
using ll = long long;

int first_at_least(const vector<ll>& prefix, ll target) {
    int left = 0, right = int(prefix.size());
    while (left < right) {
        int middle = left + (right - left) / 2;
        if (prefix[middle] >= target) right = middle;
        else left = middle + 1;
    }
    return left;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    vector<ll> prefix{0, 2, 5, 9, 14};
    cout << "answer: " << first_at_least(prefix, 8) << '\\n';
    return 0;
}`;

export default function EditorThemeSettings({prefs,setPrefs}) {
 const selected=editorTheme(prefs.editorTheme).id;
 const choose=id=>setPrefs(previous=>({...previous,editorTheme:id}));
 function navigate(event,theme) {
  if(!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
  event.preventDefault();
  const index=EDITOR_THEMES.indexOf(theme),next=event.key==='Home'?0:event.key==='End'?EDITOR_THEMES.length-1:(index+(event.key==='ArrowDown'?1:-1)+EDITOR_THEMES.length)%EDITOR_THEMES.length;
  const option=event.currentTarget.parentElement.children[next];
  option.focus({preventScroll:true});option.scrollIntoView({block:'nearest'});
  choose(EDITOR_THEMES[next].id);
 }
 return <section className="editor-theme-settings" aria-label="代码主题">
  <h2><Code2 size={19}/>代码主题</h2>
  <div className="editor-theme-layout">
   <div className="editor-theme-options" role="listbox" aria-label="代码主题选择">
    {EDITOR_THEMES.map(theme=><button type="button" key={theme.id} role="option" tabIndex={selected===theme.id?0:-1} aria-selected={selected===theme.id} title={theme.name} onClick={()=>choose(theme.id)} onKeyDown={event=>navigate(event,theme)}>
     <i style={{background:theme.colors?.bg||'var(--panel)',color:theme.colors?.keyword||'var(--accent)'}} data-effect={theme.effect} aria-hidden="true"><span>{'{ }'}</span></i>
     <span>{theme.name}</span>{selected===theme.id&&<Check size={16}/>}
    </button>)}
   </div>
   <div className="editor-theme-preview" style={editorThemeStyle(selected)}><CodeEditor value={EXAMPLE} language="cpp17" readOnly ariaLabel="代码主题预览" editorTheme={selected}/></div>
  </div>
 </section>;
}
