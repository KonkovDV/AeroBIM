import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import "./styles/design-system.css";
import "./styles/visual-language.css";
import "./styles/review-ergonomics.css";
import "./styles/product-header.css";
import "./styles/product-workplace.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Root container '#root' was not found.");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
