// Small local palettes; no extension downloads or network work while switching.
const palette=(id,name,dark,bg,fg,muted,keyword,type,string,number,fn,meta,effect)=>({id,name,dark,effect,colors:{bg,fg,muted,keyword,type,string,number,fn,meta}});
export const EDITOR_THEMES=[
 {id:'auto',name:'跟随界面',colors:null},
 // CodeMirror adaptations of the reference's visual layers. The first palette
 // is original; no Bearded theme or VS Code runtime injector is bundled.
 palette('rainbow-dark','渐变深空',true,'#18212d','#e5edf6','#94a3b8','#d99ef5','#f1ca8d','#a7d99a','#f1b17d','#88d1ed','#f39db6','rainbow'),
 palette('woodfish-dracula','Woodfish Dracula',true,'#282a36','#f8f8f2','#8b93b8','#ff79c6','#8be9fd','#f1fa8c','#bd93f9','#50fa7b','#ffb86c','rainbow'),
 palette('woodfish-black','Woodfish Black',true,'#000000','#e7e7ed','#9b9ba8','#ff8fc6','#9cdef0','#c8e99b','#cbb0f6','#8fc9ff','#ffb98d','rainbow'),
 palette('woodfish-neon','Woodfish Neon',true,'#0d0b1e','#e8e3ff','#a9a3d9','#ff2e97','#00e5ff','#b8ff5a','#b967ff','#01ffc3','#ff9e3d','rainbow'),
 palette('woodfish-light','Woodfish Light',false,'#faf8f2','#24292f','#6a737d','#b4235a','#7b3fc4','#3b7a1c','#9a6700','#1f5fbf','#9b2f94','rainbow'),
 palette('one-dark','One Dark',true,'#282c34','#abb2bf','#7f848e','#c678dd','#e5c07b','#98c379','#d19a66','#61afef','#e06c75'),
 palette('dracula','Dracula',true,'#282a36','#f8f8f2','#8b93b8','#ff79c6','#8be9fd','#f1fa8c','#bd93f9','#50fa7b','#ffb86c'),
 palette('nord','Nord',true,'#2e3440','#d8dee9','#8894aa','#81a1c1','#8fbcbb','#a3be8c','#b48ead','#88c0d0','#d08770'),
 palette('tokyo-night','Tokyo Night',true,'#1a1b26','#c0caf5','#7c86ad','#bb9af7','#2ac3de','#9ece6a','#ff9e64','#7aa2f7','#f7768e'),
 palette('catppuccin','Catppuccin Mocha',true,'#1e1e2e','#cdd6f4','#9399b2','#cba6f7','#f9e2af','#a6e3a1','#fab387','#89b4fa','#f38ba8'),
 palette('github-dark','GitHub Dark',true,'#0d1117','#e6edf3','#8b949e','#ff7b72','#ffa657','#a5d6ff','#79c0ff','#d2a8ff','#f0883e'),
 palette('monokai','Monokai',true,'#272822','#f8f8f2','#96978b','#f92672','#66d9ef','#e6db74','#ae81ff','#a6e22e','#fd971f'),
 palette('gruvbox','Gruvbox',true,'#282828','#ebdbb2','#a89984','#fb4934','#fabd2f','#b8bb26','#d3869b','#83a598','#fe8019'),
 palette('solarized-dark','Solarized Dark',true,'#002b36','#93a1a1','#7c9298','#859900','#b58900','#2aa198','#d33682','#268bd2','#cb4b16'),
 palette('ayu-dark','Ayu Dark',true,'#0b0e14','#bfbdb6','#8b929a','#ff8f40','#e6b450','#aad94c','#d2a6ff','#59c2ff','#f07178'),
 palette('rose-pine','Rosé Pine',true,'#191724','#e0def4','#908caa','#c4a7e7','#ebbcba','#f6c177','#eb6f92','#9ccfd8','#31748f'),
 palette('github-light','GitHub Light',false,'#ffffff','#24292f','#6e7781','#cf222e','#953800','#0a3069','#0550ae','#8250df','#116329'),
 palette('one-light','One Light',false,'#fafafa','#383a42','#707680','#a626a4','#986801','#50a14f','#986801','#4078f2','#e45649'),
 palette('solarized-light','Solarized Light',false,'#fdf6e3','#586e75','#7d8785','#859900','#b58900','#2aa198','#d33682','#268bd2','#cb4b16'),
 palette('ayu-light','Ayu Light',false,'#fafafa','#5c6166','#787f87','#fa8d3e','#b38b00','#6b9c27','#a37acc','#399ee6','#f07171'),
 palette('paper','Paper',false,'#f5f1e9','#3e4144','#727875','#8263a4','#896a25','#4c7a58','#a16641','#3c7094','#a85c72'),
 palette('rose-pine-dawn','Rosé Pine Dawn',false,'#faf4ed','#575279','#797593','#907aa9','#d7827e','#ea9d34','#b4637a','#286983','#56949f'),
];
export const editorTheme=id=>EDITOR_THEMES.find(theme=>theme.id===id)||EDITOR_THEMES[0];
export function editorThemeStyle(id) {
 const theme=editorTheme(id),c=theme.colors;if(!c)return {};
 return {'--editor-background':c.bg,'--editor-foreground':c.fg,'--editor-gutter':c.muted,'--editor-selection':theme.dark?'#6b7ba847':'#6585b43d','--editor-accent':c.fn,'--editor-active-line':`color-mix(in srgb, ${c.fg} 7%, transparent)`,'--editor-line':`color-mix(in srgb, ${c.fg} 16%, ${c.bg})`,'--editor-popup':`color-mix(in srgb, ${c.bg} 94%, transparent)`,'--editor-shift':theme.dark?'#c7efff':'#302458','--editor-cursor-spectrum':theme.dark?'linear-gradient(180deg,#ff92c4,#bda3ff,#8be9fd,#8be5b4,#ff92c4)':'linear-gradient(180deg,#b4235a,#7b3fc4,#1f5fbf,#0b7568,#b4235a)','--code-keyword':c.keyword,'--code-type':c.type,'--code-string':c.string,'--code-number':c.number,'--code-comment':c.muted,'--code-function':c.fn,'--code-meta':c.meta,'--code-operator':c.fg};
}

const VARIABLES=['background','foreground','gutter','selection','accent','active-line','line','popup','shift','cursor-spectrum'].map(key=>['--editor-'+key,'--theme-'+key]).concat(['keyword','type','string','number','comment','function','meta','operator'].map(key=>['--code-'+key,'--theme-'+key]));
export function applyEditorTheme(root,id) {
 const selected=editorTheme(id),style=editorThemeStyle(selected.id);
 root.dataset.editorTheme=selected.id;
 root.dataset.editorEffect=selected.effect||'none';
 for(const [local,global] of VARIABLES) {
  if(style[local])root.style.setProperty(global,style[local]);
  else root.style.removeProperty(global);
 }
}
