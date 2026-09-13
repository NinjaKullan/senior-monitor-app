/**
 * @vitest-environment node
 *
 * The robots.txt policy, pinned (seo-backlog D8). Search crawlers are never
 * refused; training-only crawlers are; the sitemap is named. A future edit
 * that blocks Googlebot by accident, or quietly widens the training set into
 * a search agent, fails here.
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const robots = readFileSync("public/robots.txt", "utf8");

/** Groups of user agents and the directives that follow them. */
function groups(): { agents: string[]; rules: string[] }[] {
  const out: { agents: string[]; rules: string[] }[] = [];
  let current: { agents: string[]; rules: string[] } | null = null;
  for (const raw of robots.split("\n")) {
    const line = raw.replace(/#.*/, "").trim();
    if (!line) continue;
    const [key, ...rest] = line.split(":");
    const value = rest.join(":").trim();
    if (/^user-agent$/i.test(key)) {
      if (!current || current.rules.length) { current = { agents: [], rules: [] }; out.push(current); }
      current.agents.push(value);
    } else if (current) current.rules.push(`${key.trim()}: ${value}`);
  }
  return out;
}

const TRAINING_ONLY = [
  "GPTBot", "ClaudeBot", "CCBot", "Bytespider", "Google-Extended",
  "Applebot-Extended", "meta-externalagent", "Amazonbot",
];
const SEARCH_AND_ANSWER = [
  "Googlebot", "Bingbot", "Applebot", "DuckDuckBot", "OAI-SearchBot",
  "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot",
];

describe("robots.txt policy (seo-backlog D8)", () => {
  it("allows everyone by default and names the sitemap", () => {
    const star = groups().find((g) => g.agents.includes("*"))!;
    expect(star.rules).toContain("Allow: /");
    expect(star.rules.some((r) => /^Disallow:/.test(r))).toBe(false);
    expect(robots).toContain("Sitemap: https://heykettle.com/sitemap.xml");
  });

  it("states the content signal: search yes, answers yes, training no", () => {
    expect(robots).toMatch(/Content-Signal:\s*search=yes,\s*ai-input=yes,\s*ai-train=no/);
  });

  it("refuses exactly the training-only crawlers, and never a search or answer agent", () => {
    const blocked = groups()
      .filter((g) => g.rules.includes("Disallow: /"))
      .flatMap((g) => g.agents)
      .sort();
    expect(blocked).toEqual([...TRAINING_ONLY].sort());
    for (const agent of SEARCH_AND_ANSWER) expect(blocked, agent).not.toContain(agent);
  });
});
