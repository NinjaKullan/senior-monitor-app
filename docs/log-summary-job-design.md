# Weekly log-summary job — design (PM, 2026-08-31, per DECISIONS 201)

Purpose: once a week, the founder learns what the site actually served
— pages and PDF downloads, counted server-side — with nothing added to
what a webserver inherently records, and no client-side anything (201,
standing law). Numbers feed the Day-30 memo and the resources
strategy.

## The constraint that shapes everything

Fly keeps container logs briefly and loses them on restart; nginx in
the site container currently logs to stdout. Anything that "reads the
logs weekly" therefore has to either (a) persist logs somewhere first
or (b) count continuously and persist only the counts. Persisting raw
logs is exactly what 201 does not want to accumulate. So: count close
to the source, keep only counts.

## Options considered

**A. Log shipper + storage (rejected).** Fly's log-shipper app to a
bucket, weekly parse. Most "standard", but it stores raw request
logs (IPs, UAs) somewhere new — the opposite of 201's keep-only-
counts posture — and adds an app + a bucket + credentials for a
weekly count.

**B. Volume + logrotate in the site container (rejected).** nginx
logs to a file on a Fly volume; weekly cron in-container summarizes
and truncates. Keeps raw logs (with IPs) at rest for up to a week,
adds state to a deliberately static site, and pins the site app to
one machine (volumes don't follow).

**C. Count-at-the-edge, ship counts to kettle-api (RECOMMENDED).**
The site container runs one tiny sidecar loop (a few lines of sh/
python in the existing image, no new app): it tails nginx's stdout
log stream locally, keeps an in-memory counter of {date, path,
status-class} for allowlisted paths (pages + PDFs; everything else
lumped as "other"), and once a day POSTs the day's counts to a new
kettle-api endpoint `POST /site-metrics/daily` authenticated by a
shared token (new Fly secret on both apps). kettle-api stores rows in
a `site_daily_counts` table (date, path, count — nothing else) and
the EXISTING scheduler sends the founder a weekly email (Resend, the
ops channel, Monday morning ET) summarizing the week: per-path counts,
week-over-week, PDF downloads called out. Raw lines are never
persisted anywhere; IPs and UAs die in-memory within the day. A
restart loses at most a partial day's counts — acceptable for a
weekly trend read, and honest about it in the email footer.

## Why C

Zero new apps, zero new storage of raw logs, counts-only at rest
(201's letter and spirit), and the weekly email rides delivery
machinery that already exists and is already tested. The site
remains a page that fetches nothing — the sidecar is server-side.

## CC handoff sketch (after dark stage lands; not before)

- Site image: add the counter sidecar (allowlist = sitemap paths +
  /resources/*/*.pdf; counter flushes daily; POST with token; fail
  silent-but-logged — a metrics hiccup must never touch serving).
- product: migration `site_daily_counts`; `POST /site-metrics/daily`
  (token check, upsert per date+path); weekly summary email into the
  existing scheduler (Monday 9am ET), founder-only, plain text.
- Tests: endpoint auth (no token = 401), upsert idempotency (same
  day re-POST doesn't double), email renders with zero data (first
  week), allowlist excludes everything not on it.
- New secret: SITE_METRICS_TOKEN on both apps (Hema sets).

## Storage budget (Supabase free plan, checked 2026-08-31)

One row per path per day, counts only. Allowlist today = 20 sitemap
pages + 8 PDFs + one "other" bucket ≈ 30 rows/day ceiling (fewer in
practice: no traffic, no row). At ~100-200 bytes/row with indexes,
a full year is ~11k rows ≈ 2 MB against the free tier's 500 MB —
under 1% per decade. sent_messages grows faster than this table.
Pressure valve if the site ever has hundreds of pages: roll dailies
into weekly rows after ~6 months and prune the dailies — the weekly
email never needed finer grain than that anyway. No storage reason
to leave the free plan.

## Founder decisions (RULED, DECISIONS 211)

1. Email lands Monday 9:00am ET.
2. Search Console stays a separate console visit; the email carries
   server counts only.
