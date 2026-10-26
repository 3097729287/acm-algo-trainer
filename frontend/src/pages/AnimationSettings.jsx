import {Play} from 'lucide-react';
import {SettingRow} from '../components/SettingsControls.jsx';
import SettingsScene from '../components/SettingsScene.jsx';

export default function AnimationSettings({prefs,setPrefs}) {
 return <section className="animation-settings" aria-label="动画设置"><h2><Play size={19}/>动画</h2>
  <SettingRow title="界面动效" hint="遵循系统减少动态效果设置。"><input className="toggle" aria-label="界面动效" type="checkbox" checked={prefs.motion!==false} onChange={event=>setPrefs(previous=>({...previous,motion:event.target.checked}))}/></SettingRow>
  <div className="animation-preview" aria-label="动画预览">{['dino','globe','orbit'].map(kind=><div key={kind}><SettingsScene kind={kind}/></div>)}</div>
 </section>;
}
