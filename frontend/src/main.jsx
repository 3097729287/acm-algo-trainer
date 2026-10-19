import React from "react";
import { createRoot } from "react-dom/client";
import App from "@/app/App.jsx";
import AccountGate from "@/accounts/AccountGate.jsx";
import "@/styles/workspace.css";
import "@/styles/refinements.css";
import "katex/dist/katex.min.css";
import "@/styles/polish.css";
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AccountGate><App /></AccountGate>
  </React.StrictMode>,
);
