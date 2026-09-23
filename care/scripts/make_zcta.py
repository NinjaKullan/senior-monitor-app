"""Build care/data/zcta.csv from the Census 2020 ZCTA Gazetteer (spec 021 §5).

    python care/scripts/make_zcta.py                 # downloads the Census file
    python care/scripts/make_zcta.py path/to/2020_Gaz_zcta_national.zip   # or .txt

The source is `2020_Gaz_zcta_national.zip`: one tab-separated text file with
GEOID, ALAND, AWATER, ALAND_SQMI, AWATER_SQMI, INTPTLAT, INTPTLONG (the last
header carries trailing spaces in the Census file). Three of those survive:
GEOID as `zcta`, INTPTLAT as `lat`, INTPTLONG as `lon`, sorted by ZCTA, about
33,000 rows. That file is checked in and bundled with the app; the app never
fetches it.

Writing the real file removes `zcta.SAMPLE`, the marker that says the checked-in
file is the 200-row hand-placed sample; the Dockerfile refuses to build while
that marker exists. Run once, by hand, from a machine that can reach census.gov.
Stdlib only.
"""

from __future__ import annotations

import csv
import io
import sys
import urllib.request
import zipfile
from collections.abc import Iterable
from pathlib import Path

SOURCE = (
    "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/"
    "2020_Gaz_zcta_national.zip"
)
DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "zcta.csv"
SAMPLE_MARKER = DATA / "zcta.SAMPLE"
EXPECTED_AT_LEAST = 30_000


def convert(lines: Iterable[str]) -> list[tuple[str, str, str]]:
    """Gazetteer lines to (zcta, lat, lon) rows, sorted by ZCTA."""
    reader = csv.reader(lines, delimiter="\t")
    header = [h.strip() for h in next(reader)]
    at = {name: header.index(name) for name in ("GEOID", "INTPTLAT", "INTPTLONG")}
    rows = []
    for fields in reader:
        if not fields:
            continue
        zcta = fields[at["GEOID"]].strip().zfill(5)
        lat = f"{float(fields[at['INTPTLAT']]):.6f}"
        lon = f"{float(fields[at['INTPTLONG']]):.6f}"
        rows.append((zcta, lat, lon))
    rows.sort()
    return rows


def read_source(path: Path | None) -> list[str]:
    if path is None:
        with urllib.request.urlopen(SOURCE, timeout=120) as response:  # noqa: S310 - fixed https URL
            blob = response.read()
    else:
        blob = path.read_bytes()
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            (name,) = [n for n in archive.namelist() if n.endswith(".txt")]
            blob = archive.read(name)
    return blob.decode("utf-8-sig").splitlines()


def write(rows: list[tuple[str, str, str]], out: Path = OUT) -> None:
    with out.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("zcta", "lat", "lon"))
        writer.writerows(rows)


def main(argv: list[str]) -> int:
    rows = convert(read_source(Path(argv[1]) if len(argv) > 1 else None))
    if len(rows) < EXPECTED_AT_LEAST:
        print(f"only {len(rows)} rows; expected the national file", file=sys.stderr)
        return 1
    write(rows)
    SAMPLE_MARKER.unlink(missing_ok=True)
    print(f"wrote {len(rows)} centroids to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
