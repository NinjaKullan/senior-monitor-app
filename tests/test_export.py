"""Acceptance criterion 7: /export.csv is the analysis input."""

from __future__ import annotations

import io
from datetime import datetime, timedelta

import pandas as pd
from fastapi.testclient import TestClient
from pandas.api.types import is_datetime64_any_dtype, is_string_dtype

from app import db
from app.timeutil import display_tz, fmt_utc
from tests.conftest import TOKEN

IST = display_tz("Asia/Kolkata")


def test_export_round_trips_into_pandas(client: TestClient, conn):
    """Columns, dtypes and instants all survive the CSV round trip."""
    base = datetime(2026, 7, 20, 8, 15, tzinfo=IST)
    for i, (who, signal) in enumerate(
        [("mom", "whatsapp"), ("dad", "news"), ("mom", "youtube")]
    ):
        db.insert_ping(conn, who, signal, fmt_utc(base + timedelta(hours=i)), None)

    resp = client.get(f"/export.csv?token={TOKEN}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    frame = pd.read_csv(io.StringIO(resp.text))
    assert list(frame.columns) == ["who", "signal", "ts_utc", "ts_ist"]
    assert len(frame) == 3
    assert is_string_dtype(frame["who"])
    assert is_string_dtype(frame["signal"])

    frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], format="%Y-%m-%dT%H:%M:%SZ", utc=True)
    frame["ts_ist"] = pd.to_datetime(frame["ts_ist"], format="ISO8601")
    assert is_datetime64_any_dtype(frame["ts_utc"])
    assert is_datetime64_any_dtype(frame["ts_ist"])

    # Same instants, different rendering; oldest first.
    assert (frame["ts_ist"].dt.tz_convert("UTC") == frame["ts_utc"]).all()
    assert frame["ts_utc"].is_monotonic_increasing
    assert frame["ts_ist"].dt.hour.tolist() == [8, 9, 10]


def test_export_carries_no_extra_columns(client: TestClient, conn):
    """The export cannot leak a field the schema does not have."""
    when = fmt_utc(datetime(2026, 7, 20, 8, 0, tzinfo=IST))
    db.insert_ping(conn, "mom", "whatsapp", when, "abc123")
    header = client.get(f"/export.csv?token={TOKEN}").text.splitlines()[0]
    assert header == "who,signal,ts_utc,ts_ist"
    assert "abc123" not in client.get(f"/export.csv?token={TOKEN}").text
