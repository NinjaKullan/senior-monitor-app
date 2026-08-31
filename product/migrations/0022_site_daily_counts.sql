-- 0022 — what the site served, counted and nothing more (DECISIONS 201/211,
-- docs/log-summary-job-design.md option C).
--
-- 201 is standing law: the site measures itself with server logs and Search
-- Console and NOTHING else, ever. The design that follows from it keeps only
-- counts — no raw request lines, no IPs, no user agents, anywhere, at any
-- point. This table is the "only counts" half made structural: three columns,
-- and there is deliberately no fourth for anything to grow into. A request
-- that arrived is a number in a bucket here and is otherwise unrecorded.
--
-- NOT family data. Every other table in this database is scoped to a family
-- and readable by that family through RLS; this one is site-wide ops data that
-- belongs to the founder alone. So it takes the opposite posture: RLS on, and
-- NO grants to anon or authenticated at all. The service role writes it (the
-- endpoint) and reads it (the weekly email); a family session cannot see that
-- this table exists, which is correct — page counts are not theirs and say
-- nothing about them. test_rls's privilege snapshot pins the absence.

create table site_daily_counts (
    -- The site's day in UTC, the counter's own reckoning. A day boundary
    -- that drifts by a few hours at the edges is immaterial to a weekly
    -- trend read, and a timezone column would be a fourth field this
    -- table has no business carrying.
    day   date    not null,
    -- An ALLOWLISTED path, or the literal 'other'. The allowlist lives in the
    -- counter (site/counter/kettle_counter.py) and in kettle/site_metrics.py,
    -- and anything off it is lumped into one bucket before it ever leaves the
    -- site container — so an unexpected path cannot become a row here, and a
    -- URL someone probed us with is never written down.
    path  text    not null check (char_length(path) <= 200),
    count integer not null default 0 check (count >= 0),
    primary key (day, path)
);

alter table site_daily_counts enable row level security;

-- The weekly email's once-only key. The ops loop runs every minute; without a
-- durable record of which weeks have been summarised, a Monday 9am window
-- would send once a minute for an hour, and a restart inside the window would
-- send again. One row per week sent, claimed atomically by the insert itself.
create table site_weekly_sends (
    week_start date        primary key,
    sent_utc   timestamptz not null default now()
);

alter table site_weekly_sends enable row level security;
