"""Kettle product backend — multi-tenant core (spec 002).

Shares no runtime with the pilot in `app/`: the pilot is a running experiment
and stays frozen. Patterns carried over (signal allowlisting, UTC discipline,
dedupe, heartbeat idempotency) are re-implemented here against Postgres.
"""
