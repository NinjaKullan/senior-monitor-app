/**
 * @vitest-environment node
 *
 * DECISIONS 148/168 — the redirect-loop class of outage, held shut.
 *
 * The heykettle.com outage happened because a comment encoded a host-dispatch
 * rule nginx does not have: `server_name _` is NOT a default. With no
 * `default_server` marked, nginx routes every unmatched Host to the FIRST
 * server block in the file — which was the fly.dev→canonical 301, so the
 * canonical domain redirected to itself forever, and nothing in the suite
 * asked a single Host-shaped question.
 *
 * This file asks them. It parses the real nginx.conf and simulates nginx's
 * documented dispatch — exact server_name match, else the default_server
 * block, else the first block in the file — then follows redirects across
 * hosts and asserts every journey terminates. The simulator's three-line rule
 * was validated against a real nginx 1.24 running this exact config
 * (2026-08-23, DECISIONS 168): healthy config → 200/301/200 exactly as
 * asserted here; with `default_server` removed, the real binary reproduced
 * the ERR_TOO_MANY_REDIRECTS loop and so does the simulation. If the config
 * grows a shape the parser does not recognise, the parser throws rather than
 * guessing — re-validate against a real binary before teaching it new tricks.
 *
 * The blog (DECISIONS 174) taught it one new trick, re-validated the same way
 * (real nginx 1.24 over the blog directory layout, 2026-08-26): the file
 * model below mirrors `try_files $uri $uri/ =404` with `index index.html` —
 * a file 200s, a directory without its trailing slash 301s to the slash form,
 * a directory with one serves its index, anything else 404s. And the
 * redirect's SHAPE is load-bearing: with `absolute_redirect off` the real
 * binary writes `Location: /blog/`; without it, `http://<host>:8080/blog/` —
 * nginx's own scheme and port, which behind Fly's TLS proxy is a URL nobody
 * can follow. The simulation reproduces both forms so the pin below fails
 * the way production would.
 */
import { existsSync, readFileSync, statSync } from "node:fs";
import { describe, expect, it } from "vitest";

const CANONICAL = "heykettle.com";
const OLD_HOST = "kettle-site.fly.dev";
const WWW = "www.heykettle.com";
/** Post #1's canonical path (DECISIONS 174), slash-less as published. */
const ARTICLE = "/blog/the-call-ive-rehearsed-and-never-made";

interface ServerBlock {
  index: number;
  serverNames: string[];
  isDefault: boolean;
  servesFiles: boolean;
  rootRedirect: string | null; // the `return 301 <target>` of `location /`
  hasHealthz: boolean;
  absoluteRedirectOff: boolean;
}

function parseBlocks(conf: string): ServerBlock[] {
  const blocks: ServerBlock[] = [];
  const starts = [...conf.matchAll(/^server\s*\{/gm)];
  if (starts.length === 0) throw new Error("no server blocks found");
  for (const [index, match] of starts.entries()) {
    // Walk braces from the block's opening `{` to its matching close.
    let depth = 0;
    let end = match.index!;
    for (let i = conf.indexOf("{", match.index!); i < conf.length; i++) {
      if (conf[i] === "{") depth++;
      if (conf[i] === "}") depth--;
      if (depth === 0) {
        end = i;
        break;
      }
    }
    const body = conf.slice(match.index!, end + 1);

    const listen = body.match(/^\s*listen\s+([^;]+);/m);
    if (!listen) throw new Error(`server block ${index} has no listen line`);
    const nameLine = body.match(/^\s*server_name\s+([^;]+);/m);
    if (!nameLine) throw new Error(`server block ${index} has no server_name`);

    const rootLocation = body.match(
      /location\s+\/\s*\{([\s\S]*?)\n\s*\}/,
    );
    if (!rootLocation) throw new Error(`server block ${index} has no location /`);
    const redirect = rootLocation[1].match(/return\s+301\s+([^;]+);/);
    const serves = /try_files/.test(rootLocation[1]);
    if (!redirect && !serves) {
      throw new Error(`server block ${index}: location / neither redirects nor serves`);
    }

    blocks.push({
      index,
      serverNames: nameLine[1].trim().split(/\s+/),
      isDefault: /\bdefault_server\b/.test(listen[1]),
      servesFiles: serves,
      rootRedirect: redirect ? redirect[1].trim() : null,
      hasHealthz: /location\s+\/healthz/.test(body),
      absoluteRedirectOff: /^\s*absolute_redirect\s+off;/m.test(body),
    });
  }
  return blocks;
}

const conf = readFileSync("nginx.conf", "utf8");
const blocks = parseBlocks(conf);

/** nginx's documented dispatch, stated where 148's wrong comment once lived:
 * exact server_name match; else the default_server block; else — the trap —
 * the FIRST block in the file. `server_name _` is a name like any other. */
function dispatch(host: string): ServerBlock {
  const exact = blocks.find((b) => b.serverNames.includes(host));
  if (exact) return exact;
  const fallback = blocks.find((b) => b.isDefault);
  return fallback ?? blocks[0];
}

/**
 * The serving block's file model: `try_files $uri $uri/ =404` with the default
 * `index index.html`, resolved against `public/` — the source the build copies
 * into the image verbatim. Deliberately NOT `dist/`: reading a build product
 * makes the verdict depend on when the build last ran (failure family 1). The
 * two paths vite itself writes at build are listed by hand.
 */
const DOCROOT = "public";
const BUILT_AT_BUILD_TIME = new Set(["/", "/index.html"]);

function serveStatus(path: string): { status: number; location: string | null } {
  if (BUILT_AT_BUILD_TIME.has(path)) return { status: 200, location: null };
  const fsPath = DOCROOT + path;
  if (existsSync(fsPath) && statSync(fsPath).isFile()) return { status: 200, location: null };
  if (existsSync(fsPath) && statSync(fsPath).isDirectory()) {
    // The index module: a directory reached without its trailing slash is a
    // 301 to the slash form; with it, the directory's index.html serves.
    if (!path.endsWith("/")) return { status: 301, location: `${path}/` };
    if (existsSync(`${fsPath}index.html`)) return { status: 200, location: null };
  }
  return { status: 404, location: null };
}

function respond(
  host: string,
  path: string,
): { status: number; location: string | null } {
  const block = dispatch(host);
  if (path === "/healthz" && block.hasHealthz) return { status: 200, location: null };
  if (block.rootRedirect) {
    return {
      status: 301,
      location: block.rootRedirect.replace("$request_uri", path),
    };
  }
  const served = serveStatus(path);
  if (served.status === 301 && !block.absoluteRedirectOff) {
    // Without `absolute_redirect off`, the real binary writes the Location
    // from its own listen view — wrong scheme, unreachable port, behind the
    // TLS proxy (validated 2026-08-26). Reproduced so the pin can fail.
    return { status: 301, location: `http://${host}:8080${served.location}` };
  }
  return served;
}

/** Follow redirects across hosts, the way a browser did on 2026-08-22. */
function follow(host: string, path: string) {
  const hops: { host: string; status: number; location: string | null }[] = [];
  let at = { host, path };
  for (let hop = 0; hop < 5; hop++) {
    const response = respond(at.host, at.path);
    hops.push({ host: at.host, ...response });
    if (response.status !== 301) return hops;
    // A relative Location (the absolute_redirect-off form) resolves against
    // the origin the browser is already on, which is the point of it.
    const target = new URL(response.location!, `https://${at.host}`);
    at = { host: target.host, path: target.pathname };
  }
  return hops; // 5 hops of 301s: the loop the asserts below refuse
}

describe("canonical-host behavior (DECISIONS 148/168)", () => {
  it("GET / with Host heykettle.com returns 200, first try", () => {
    expect(follow(CANONICAL, "/")).toEqual([
      { host: CANONICAL, status: 200, location: null },
    ]);
  });

  it("the old fly.dev host is exactly one 301 to the canonical root", () => {
    const hops = follow(OLD_HOST, "/");
    expect(hops.length).toBe(2); // one redirect, then the page — no chain
    expect(hops[0]).toEqual({
      host: OLD_HOST,
      status: 301,
      location: `https://${CANONICAL}/`,
    });
    expect(hops[1].status).toBe(200);
  });

  it("www.heykettle.com serves the page directly — pinned as production-correct", () => {
    // www is deliberately NOT a named host: it falls to the default_server
    // block and serves a 200 with no redirect. If someone names www in the
    // config, this pin fails and the behavior gets re-decided on purpose.
    expect(blocks.some((b) => b.serverNames.includes(WWW))).toBe(false);
    expect(follow(WWW, "/")).toEqual([{ host: WWW, status: 200, location: null }]);
  });

  it("the serving block, and only the serving block, is the declared default server", () => {
    const defaults = blocks.filter((b) => b.isDefault);
    expect(defaults.length).toBe(1);
    expect(defaults[0].servesFiles).toBe(true);
    expect(defaults[0].rootRedirect).toBeNull();
  });

  it("no Host can loop: every journey ends in a 200 within two hops", () => {
    const hosts = [
      CANONICAL,
      WWW,
      OLD_HOST,
      ...blocks.flatMap((b) => b.serverNames).filter((n) => n !== "_"),
      "unmatched.example",
    ];
    for (const host of hosts) {
      const hops = follow(host, "/");
      expect(hops.length, `${host} redirected ${hops.length - 1} times`).toBeLessThanOrEqual(2);
      expect(hops.at(-1)!.status, `${host} never reached a page`).toBe(200);
    }
  });

  it("the old host answers its own health check instead of redirecting it", () => {
    // DECISIONS 142/158: a health endpoint that 301s reports on the wrong
    // machine.
    expect(respond(OLD_HOST, "/healthz")).toEqual({ status: 200, location: null });
  });

  it("serves /blog/ and the article on the canonical host, first try", () => {
    for (const path of ["/blog/", `${ARTICLE}/`]) {
      expect(follow(CANONICAL, path)).toEqual([
        { host: CANONICAL, status: 200, location: null },
      ]);
    }
  });

  it("adds the trailing slash in exactly one relative hop", () => {
    for (const path of ["/blog", ARTICLE]) {
      const hops = follow(CANONICAL, path);
      expect(hops).toEqual([
        { host: CANONICAL, status: 301, location: `${path}/` },
        { host: CANONICAL, status: 200, location: null },
      ]);
    }
  });

  it("the serving block declares absolute_redirect off — the slash 301 must be relative", () => {
    // Without it the real binary writes `http://<host>:8080/blog/` — its own
    // scheme and listen port, unreachable behind the TLS proxy (validated
    // against nginx 1.24, 2026-08-26). Removing the directive fails here.
    const serving = blocks.find((b) => b.servesFiles)!;
    expect(serving.absoluteRedirectOff).toBe(true);
  });

  it("the old host forwards a blog path whole, then the slash hop lands it", () => {
    const hops = follow(OLD_HOST, ARTICLE);
    expect(hops[0]).toEqual({
      host: OLD_HOST,
      status: 301,
      location: `https://${CANONICAL}${ARTICLE}`,
    });
    expect(hops[1]).toEqual({ host: CANONICAL, status: 301, location: `${ARTICLE}/` });
    expect(hops[2]).toEqual({ host: CANONICAL, status: 200, location: null });
    expect(hops).toHaveLength(3);
  });

  it("an unknown blog path is a 404, not a fallback render", () => {
    expect(follow(CANONICAL, "/blog/a-post-that-does-not-exist/")).toEqual([
      { host: CANONICAL, status: 404, location: null },
    ]);
  });

  it("the parser saw the config it was validated against", () => {
    // Two blocks, redirect-first: the exact shape the real-nginx validation
    // ran on. A restructure lands here first, as a prompt to re-validate the
    // simulator against a real binary rather than trusting it blind.
    expect(blocks.length).toBe(2);
    expect(blocks[0].rootRedirect).not.toBeNull();
    expect(blocks[0].serverNames).toEqual([OLD_HOST]);
    expect(blocks[1].servesFiles).toBe(true);
  });
});
