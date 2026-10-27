import {createContext,useContext} from 'react';
const Context=createContext('number');
export function DifficultyDisplayProvider({mode,children}){return <Context.Provider value={mode==='text'?'text':'number'}>{children}</Context.Provider>;}
export const useDifficultyDisplay=()=>useContext(Context);
