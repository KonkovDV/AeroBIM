import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { browserDensityStore, documentDensityTarget, initDensity } from "./lib/ui-density";
import "./styles.css";
import "./styles/design-system.css";
import "./styles/visual-language.css";
import "./styles/review-ergonomics.css";
import "./styles/product-header.css";
import "./styles/product-workplace.css";
import "./styles/force-light.css";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Root container '#root' was not found.");
}

// Плотность применяется до первой отрисовки: без мигания отступов на старте.
initDensity(documentDensityTarget(), browserDensityStore());

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
