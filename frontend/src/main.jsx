import React from "react";
import { createRoot } from "react-dom/client";
import { BackgroundPlayback } from "@/components/BackgroundPlaylist.jsx";
import App from "@/app/App.jsx";
import AccountGate from "@/accounts/AccountGate.jsx";
import "@/styles/workspace.css";
import "@/styles/refinements.css";
import "katex/dist/katex.min.css";
import "@/styles/polish.css";
import "@/styles/unified.css";
createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AccountGate><BackgroundPlayback/><App /></AccountGate>
  </React.StrictMode>,
);
