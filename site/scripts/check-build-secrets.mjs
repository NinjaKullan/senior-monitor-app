#!/usr/bin/env node
/**
 * AC7 — prove the shipped bundle carries no secret beyond the publishable key.
 *
 * This app is a static site: every byte of `dist/` is downloadable by anyone who
 * loads it. The Supabase URL and publishable key belong there; the service key
 * bypasses RLS entirely and must never appear. Rather than trust that nobody
 * pastes one in, this greps the actual build output — and decodes any JWT it
 * finds, because a service key is only distinguishable from a publishable one
 * by the `role` claim inside it.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const DIST = process.argv[2] ?? "dist";

const LITERAL_PATTERNS = [
  { name: "service_role claim", re: /service_role/ },
  { name: "new-style secret key", re: /\bsb_secret_[A-Za-z0-9_-]+/ },
  { name: "service key env name", re: /SUPABASE_SERVICE(_ROLE)?_KEY/ },
  { name: "postgres connection string", re: /postgres(ql)?:\/\/[^\s"']*:[^\s"'@]*@/ },
  { name: "Twilio auth token env name", re: /TWILIO_AUTH_TOKEN/ },
  { name: "ntfy topic env name", re: /NTFY_TOPIC/ },
];

const JWT = /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g;

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

function jwtRole(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(Buffer.from(payload, "base64").toString("utf8")).role ?? null;
  } catch {
    return null;
  }
}

let files;
try {
  files = walk(DIST);
} catch {
  console.error(`No build output at ${DIST}/ — run \`npm run build\` first.`);
  process.exit(1);
}

const findings = [];
for (const file of files) {
  const text = safeRead(file);
  if (text === null) continue;
  for (const { name, re } of LITERAL_PATTERNS) {
    if (re.test(text)) findings.push(`${file}: ${name}`);
  }
  for (const token of text.match(JWT) ?? []) {
    const role = jwtRole(token);
    if (role && role !== "anon") findings.push(`${file}: JWT with role="${role}"`);
  }
}

function safeRead(file) {
  try {
    return readFileSync(file, "utf8");
  } catch {
    return null;
  }
}

if (findings.length > 0) {
  console.error("Secret material found in the build output:");
  for (const finding of findings) console.error(`  - ${finding}`);
  process.exit(1);
}
console.log(`No secret material in ${files.length} built files.`);
