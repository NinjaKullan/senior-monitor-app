// Build-time prerender (spec 006 AC9).
//
// The page must read with JavaScript off: someone on a slow connection, a
// locked-down work laptop or a text browser is exactly the anxious relative
// this product is for, and an empty <div id="root"> serves them nothing. So the
// React tree is rendered to HTML at build time and injected into dist/index.html,
// and the client hydrates it rather than creating it.
//
// scripts/check-prerender.mjs then reads the built file back and fails if the
// copy is not in it — a prerender that silently stopped running would otherwise
// ship an empty page that looks fine to everyone whose browser runs scripts.
import { readFile, writeFile, rm } from "node:fs/promises";

const { render } = await import("./dist-ssr/entry-server.js");
const template = await readFile("dist/index.html", "utf8");

if (!template.includes("<!--app-html-->")) {
  throw new Error("dist/index.html has no <!--app-html--> placeholder to fill");
}

await writeFile("dist/index.html", template.replace("<!--app-html-->", render()));
await rm("dist-ssr", { recursive: true, force: true });
console.log("prerendered dist/index.html");
