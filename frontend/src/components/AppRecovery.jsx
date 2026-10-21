import {Component} from 'react';
import {RefreshCw} from 'lucide-react';

/** Keep a render failure visible and recoverable without deleting local state. */
export default class AppRecovery extends Component {
  state={failed:false,generation:0};
  static getDerivedStateFromError(){return {failed:true};}
  componentDidCatch(error){console.error('TB render failure',error?.name||'Error');}
  render(){
    if(this.state.failed)return <main className="app-recovery" role="alert"><h1>界面暂时无法显示</h1><button type="button" onClick={()=>this.setState(previous=>({failed:false,generation:previous.generation+1}))}><RefreshCw size={17}/>恢复界面</button></main>;
    return <span key={this.state.generation} style={{display:'contents'}}>{this.props.children}</span>;
  }
}
