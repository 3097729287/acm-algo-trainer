// Luogu's observed 2026 ComboBox: text div, teleported dropdown, native click.
export function luoguComboFixture(current='C++23', labels=['C++98','C++14','C++17','C++20','C++23','Python 3','Java 21']) {
  const ids={'C++98':1,'C++14':2,'C++17':12,'C++20':27,'C++23':28,'Python 3':7,'Java 21':8};
  const options=labels.map(label=>({label,id:ids[label]}));
  return {
    currentId:ids[current],
    html:`<div data-v-fixture-combo class="combo-wrapper lang-select light-black inline"><div class="text lform-size-middle">${current}</div><span class="arrow">⌄</span><div class="ruler"></div></div>`,
    script:`window.fixtureLang=${ids[current]};window.fixtureLanguageClicks=0;
      document.querySelector('.combo-wrapper.lang-select .text').onclick=()=>{
        window.fixtureLanguageClicks++;
        setTimeout(()=>{
          const menu=document.createElement('div');menu.className='dropdown';menu.setAttribute('data-v-fixture-combo','');
          const list=document.createElement('ul');menu.appendChild(list);
          for(const option of ${JSON.stringify(options)}){
            const item=document.createElement('li');item.textContent=option.label;
            item.onclick=()=>{document.querySelector('.combo-wrapper.lang-select .text').textContent=option.label;window.fixtureLang=option.id;menu.remove()};
            list.appendChild(item);
          }
          document.body.appendChild(menu);
        },50);
      };`,
  };
}
