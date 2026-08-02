import { hydrateRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

// Hydrate rather than render: the HTML is prerendered at build time, so the page
// reads with JavaScript off (AC9) and the script only wakes the tabs and the
// form up.
hydrateRoot(document.getElementById("root")!, <App />);
