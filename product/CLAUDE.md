# product/ — the backend, and the laws that live closest to the data

Loaded when you are working under `product/`. Root `CLAUDE.md` carries the product
law that binds every surface; this file carries what only applies here.

## Running anything

- **Postgres is not up.** `service postgresql start`, then `pg_isready`. On a fresh
  container that is still not enough — the role and the database do not exist yet, so
  `pg_isready` says "accepting connections" while the suite skips anyway. The rest of
  the recipe is in `product/README.md`: `su postgres -c "psql -c \"alter user postgres
  with password 'postgres'\""` then `su postgres -c "createdb kettle_test"`.
- **Run with `KETTLE_REQUIRE_POSTGRES=1`.** Without it a missing database makes the
  suite *skip* and report "N passed" while proving nothing — the single most likely
  way to report a false green here. CI sets it (`.github/workflows/ci.yml`, with a
  Postgres service container). Read `docs/failure-families.md` §1 before you believe
  any product-suite result.
- **Use `.venv/bin/python -m pytest` and `.venv/bin/ruff`** — system Python has
  neither installed. A fresh container has no `.venv`: `python3 -m venv .venv &&
  .venv/bin/pip install -r requirements-dev.txt -r product/requirements-dev.txt`.
- **Docker is unavailable.** Local Postgres plus `product/migrations/local/`'s Supabase
  shim is the substitute. Fly and Supabase deploys cannot run from here.

## The laws that are enforced in this tree

- **Three fields, and they are literally three.** A signal row is `who`, `signal`, and
  the server's timestamp. Anything else arriving at the door is dropped there, not
  stored and filtered later. The site says this in public ("Three fields. Nothing
  else."), so the schema is a promise, not an implementation detail.
- **Alarm-grade is a vocabulary, not a mood.** Which signals may anchor reassurance or
  alarm is decided in the spec and enforced in code; a charger event can corroborate
  and can never green a verify check. Law #6 in the root file is the general form —
  household-grade signals never stand in for a person.
- **The copy law reaches every string a human sees**, including ladder and digest
  messages: no urgency, no diagnosis, no medical or surveillance vocabulary, no
  person-verdict. `product/tests/test_digest_copy.py` and `test_ladder_copy.py` hold
  it. App names are mechanism vocabulary and belong only where the mechanism is being
  described — never in a sentence about someone's day.
- **Tokens are per device, never per family, never guessable**, and humans never type
  them. `product/kettle/tokens.py` says why.

## Where the rest is written

`product/README.md` (what is stored, isolation, endpoints, the ladder, the forge),
`specs/` for the specs themselves, `docs/failure-families.md` for the traps,
`specs/DECISIONS.md` for rulings — the archive holds 1 through 120.
