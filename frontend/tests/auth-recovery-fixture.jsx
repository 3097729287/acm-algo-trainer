import React from 'react';
import { createRoot } from 'react-dom/client';
import AccountGate from '../src/accounts/AccountGate.jsx';
createRoot(document.getElementById('root')).render(<AccountGate><div data-testid="unlocked-workspace">Isolated authenticated workspace<textarea aria-label="Isolated draft"/></div></AccountGate>);
