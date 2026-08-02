import { renderToString } from "react-dom/server";
import App from "./App";

/** Build-time render. `prerender.mjs` writes the result into dist/index.html. */
export function render(): string {
  return renderToString(<App />);
}
