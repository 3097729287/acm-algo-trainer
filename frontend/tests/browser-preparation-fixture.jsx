import React from 'react';
import { createRoot } from 'react-dom/client';
import BrowserPreparation from '../src/pages/BrowserPreparation.jsx';
import { request } from '../src/api/client.js';
import '../src/styles/workspace.css';
createRoot(document.getElementById('root')).render(<React.StrictMode><BrowserPreparation enabled api={(path,body)=>request(path,body,'preparation-fixture')}/></React.StrictMode>);
