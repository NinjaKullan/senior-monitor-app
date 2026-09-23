"""Centroids, distance, which states to read, and the shipped data (spec 021 §5)."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

from care import geo
from care.geo import Centroids, miles_between, normalize_zip, state_for

CARE = Path(__file__).resolve().parent.parent


def test_prefixes_to_states():
    for zip5, state in [
        ("27502", "NC"), ("28273", "NC"), ("29715", "SC"), ("43215", "OH"), ("02139", "MA"),
        ("05501", "MA"), ("20001", "DC"), ("20166", "VA"), ("73301", "TX"), ("73102", "OK"),
        ("88501", "TX"), ("96813", "HI"), ("99501", "AK"), ("00901", "PR"), ("10001", "NY"),
    ]:
        assert state_for(zip5) == state, zip5
    for bad in ("00000", "09001", "34001", "2750", "abcde"):  # unassigned or military or junk
        assert state_for(bad) is None, bad


def test_great_circle_miles():
    # Raleigh to Charlotte is about 130 miles as the crow flies.
    assert 125 < miles_between((35.7796, -78.6382), (35.2271, -80.8431)) < 135
    assert miles_between((35.0, -80.0), (35.0, -80.0)) == 0


def test_states_within_the_radius(centroids):
    assert centroids.states_within("27502", 15) == ["NC"]
    assert centroids.states_within("28273", 15) == ["NC", "SC"]
    assert centroids.states_within("29715", 10) == ["SC", "NC"]  # own state first
    assert centroids.states_within("99999", 15) == []


def test_cms_zip_fields():
    assert normalize_zip("27513-4410") == "27513"
    assert normalize_zip("275134410") == "27513"
    assert normalize_zip("2139") == "02139"
    assert normalize_zip(27502) == "27502"
    assert normalize_zip("") is None and normalize_zip(None) is None


# --- the shipped centroid file -----------------------------------------------------------


def test_the_shipped_file_is_three_columns_and_honest_about_what_it_is():
    path = CARE / "data" / "zcta.csv"
    rows = list(csv.reader(path.open()))
    assert rows[0] == ["zcta", "lat", "lon"]
    body = rows[1:]
    assert all(len(r) == 3 and len(r[0]) == 5 and r[0].isdigit() for r in body)
    assert [r[0] for r in body] == sorted({r[0] for r in body})
    sample = (CARE / "data" / "zcta.SAMPLE").exists()
    if sample:
        assert len(body) == 200, "the marker says sample; the file is not the sample"
    else:
        assert len(body) >= 30_000, "no sample marker, but not the national file either"
    shipped = Centroids.load(path)
    # The page's own examples are answerable (site PAGE_EXAMPLE_1 and _3).
    assert shipped.point("43215") and shipped.point("27502")
    assert shipped.states_within("27502", 15)[0] == "NC"


def test_the_image_refuses_to_build_from_the_sample():
    dockerfile = (CARE / "Dockerfile").read_text()
    assert "test ! -f care/data/zcta.SAMPLE" in dockerfile
    assert "--no-access-log" in dockerfile
    ignored = (CARE / ".dockerignore").read_text().split()
    assert "tests" in ignored and "scripts" in ignored


def test_fly_config():
    fly = (CARE / "fly.toml").read_text()
    assert 'app = "kettle-care"' in fly
    assert 'primary_region = "iad"' in fly
    assert 'size = "shared-cpu-1x"' in fly
    assert "[env]" not in fly and "secret" not in fly.lower().replace("no secrets", "")


# --- the script that makes it ------------------------------------------------------------


@pytest.fixture
def make_zcta():
    spec = importlib.util.spec_from_file_location("make_zcta", CARE / "scripts" / "make_zcta.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GAZETTEER = [
    "GEOID\tALAND\tAWATER\tALAND_SQMI\tAWATER_SQMI\tINTPTLAT\tINTPTLONG                 ",
    "27502\t130000000\t2000000\t50.2\t0.8\t35.723612\t-78.866301",
    "00601\t166000000\t800000\t64.3\t0.3\t18.180555\t-66.749961",
    "",
]


def test_the_script_keeps_three_columns_sorted(make_zcta, tmp_path):
    rows = make_zcta.convert(GAZETTEER)
    assert rows == [("00601", "18.180555", "-66.749961"), ("27502", "35.723612", "-78.866301")]
    out = tmp_path / "zcta.csv"
    make_zcta.write(rows, out)
    assert out.read_text().splitlines() == [
        "zcta,lat,lon", "00601,18.180555,-66.749961", "27502,35.723612,-78.866301"
    ]
    assert Centroids.load(out).point("27502") == (35.723612, -78.866301)


def test_the_script_names_the_census_file(make_zcta):
    assert make_zcta.SOURCE.endswith("/2020_Gazetteer/2020_Gaz_zcta_national.zip")
    assert make_zcta.SOURCE.startswith("https://www2.census.gov/")
    assert make_zcta.OUT == geo.DATA
