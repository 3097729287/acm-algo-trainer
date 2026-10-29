import {createContext,useContext} from 'react';
export const FeatureVisibilityContext=createContext(()=>true);
export const useFeatureVisibility=()=>useContext(FeatureVisibilityContext);
