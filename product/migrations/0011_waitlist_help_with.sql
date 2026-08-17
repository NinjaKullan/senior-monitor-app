-- 0011 — the waitlist's one optional sentence (beta conversion, QUESTIONS 129).
--
-- "What would you most like Kettle to help with?" — the first free text a
-- stranger can leave anywhere in this product, and it changes nothing about
-- the table's posture: no policy exists, so RLS denies anon and authenticated
-- outright; 0009's direct revokes stand; the API's service role remains the
-- only writer, and nothing client-side ever reads the table (the webapp's
-- declared read surface is tested not to learn its name).
--
-- The length cap lives here as well as in the API (which truncates before
-- insert): the CHECK is the wall that makes an unbounded blob unrepresentable
-- even if some future code path forgets the trim. Nullable on purpose — the
-- field is optional, and an empty answer is stored as absence, not as ''.

alter table waitlist
    add column help_with text
    check (help_with is null or char_length(help_with) <= 1000);
