# Beta price copy and the waitlist ping (brief for Claude Code)

Two founder rulings from the growth session, 2026-10-18 (DECISIONS 365).

## 1. Price: first year free, then $10 a month per family, locked

The site says "$10 a month per loved one". The ruling is: free for the first
year, then $10 a month per family, up to two parents, held at that rate for as
long as the family stays. Per family, never per parent or per member (358
already ruled per circle).

Change every place the old line lives:

* `site/src/copy.ts` line ~237 (the founding-rate sentence) and any test that
  pins it.
* `docs/beta-invitation.md` (three mentions: the price line as sent, and the
  two invitation bodies).
* The writers' brief under docs/ that quotes the price (grep "$10").

Suggested sentence, PM copy, subject to the copy laws (LAW-1 to LAW-10,
docs/feature-backlog.md §5): "Free for your first year. After that, $10 a month
for your family, up to two parents, held at that rate for as long as you stay."
Run the site's copy-ban scan; "honoured" with the British spelling goes if the
scan or the US-market ruling objects.

## 2. Waitlist signups ping the founder

`POST` to the waitlist (product/kettle/waitlist.py) stores the row and tells no
one. Add one ntfy post through the existing transport (product/kettle/notify.py,
`NTFY_TOPIC`) on every new signup: the text is the count and the help_with
value only, never the email or the phone ("Waitlist: new signup (#12), help
with: Mom lives alone"). Repeat signups (upsert of an existing email) do not
ping. Failure to post must not fail the signup. One test for the ping, one for
the repeat case, one for the no-personal-data rule, each planted and caught.

Push needed: yes, and a kettle-api deploy for §2 (founder). No migration.
