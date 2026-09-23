"""find_care (spec 021 §3.1, §4; acceptance §8.1 to §8.4).

Every expected sentence is written out whole: §8.1 asks for §4 character for
character, and a test that rebuilt the sentence from the template would pass
on a template that drifted.
"""

from __future__ import annotations

from care import answers as a
from care import copy as text

SOURCE_NH = (
    "Source: Medicare Care Compare, last updated August 1, 2026. "
    "Ratings are Medicare's, not ours."
)
SOURCE_HH = (
    "Source: Medicare Care Compare, last updated May 27, 2026. "
    "Ratings are Medicare's, not ours."
)
CALL = "The next step is a phone call to the provider. Ask about openings, cost, and a visit."


def test_nursing_homes_near_apex_read_exactly_as_section_4(ask, fake):
    """§8.1: at most 8, nearest first, every sentence §4's, the fixture's date."""
    answer = ask("find_care", kind="nursing home", zip="27502")
    assert answer == "\n".join(
        [
            "Apex Ridge Center, Apex, under a mile away. CMS rates it 2 of 5 overall. "
            "(919) 555 0102.",
            "Pine Hollow Health and Rehabilitation, Apex, about 1 mile away. CMS rates it 4 "
            "of 5 overall. (919) 555 0101.",
            "Cary Oaks Nursing and Rehab, Cary, about 6 miles away. CMS has not rated it "
            "overall yet. (919) 555 0103.",
            "Western Wake Care, Cary, about 6 miles away. CMS rates it 3 of 5 overall. "
            "(919) 555 0108.",
            "St. Mary's Care Center, Cary, about 6 miles away. CMS rates it 5 of 5 overall. "
            "(919) 555 0104.",
            "Holly Springs Manor, Holly Springs, about 7 miles away. CMS rates it 3 of 5 "
            "overall. (919) 555 0105.",
            "Green Level Health, Cary, about 7 miles away. CMS rates it 2 of 5 overall. "
            "(919) 555 0109.",
            "Morrisville Gardens, Morrisville, about 10 miles away. CMS rates it 1 of 5 "
            "overall. (919) 555 0106.",
            "",
            "There are 2 more within 15 miles. Ask for a smaller distance or a minimum rating "
            "to narrow it.",
            "",
            SOURCE_NH,
            CALL,
        ]
    )
    # Only North Carolina was read: Apex is nowhere near a state line.
    states = {r.url.params["conditions[0][value]"] for r in fake.data_requests()}
    assert states == {"NC"}


def test_home_health_near_apex(ask):
    answer = ask("find_care", kind="home health agency", zip="27502")
    assert answer == "\n".join(
        [
            "Apex Home Care, Apex, under a mile away. CMS rates its quality of patient care "
            "3.5 of 5. (919) 555 0301.",
            "Triangle Home Health Services, Cary, about 6 miles away. CMS rates its quality of "
            "patient care 4 of 5. (919) 555 0302.",
            "Holly Springs Home Health, Holly Springs, about 7 miles away. CMS has not rated "
            "its quality of patient care yet. (919) 555 0303.",
            "",
            SOURCE_HH,
            CALL,
        ]
    )


def test_every_accepted_kind_word(ask):
    for kind in ("nursing home", "Nursing Homes", "home health", "home health agency", "home care"):
        assert ask("find_care", kind=kind, zip="27502").endswith(CALL), kind


def test_distance_home_health_by_zip_centroid_nursing_home_by_cms_coordinates(centroids, fake):
    """§8.2, at the function that decides where a provider is."""
    nh = {r["provider_name"]: r for r in fake.rows("4pq5-n9py", "NC")}
    hh = {r["provider_name"]: r for r in fake.rows("6jpm-sxkc", "NC")}
    # Home health: CMS gives no coordinates; ZIP+4 is cut to its ZIP's centroid.
    assert a.provider_point(hh["TRIANGLE HOME HEALTH SERVICES"], a.HOME_HEALTH, centroids) == (
        centroids.point("27513")
    )
    # A nursing home by its own CMS latitude and longitude, not its ZIP's.
    pine = a.provider_point(nh["PINE HOLLOW HEALTH AND REHABILITATION"], a.NURSING, centroids)
    assert pine == (35.73, -78.85) != centroids.point("27502")
    # Null coordinates fall back to the ZIP centroid.
    gardens = a.provider_point(nh["MORRISVILLE GARDENS"], a.NURSING, centroids)
    assert gardens == centroids.point("27560")


def test_distance_rules_reach_the_answer(ask):
    """§8.2 through the tool: the null-coordinate home is placed at 27560's
    centroid (about 10 miles), and the agency at 27513's (about 6)."""
    homes = ask("find_care", kind="nursing home", zip="27502")
    assert "Morrisville Gardens, Morrisville, about 10 miles away." in homes
    agencies = ask("find_care", kind="home health", zip="27502")
    assert "Triangle Home Health Services, Cary, about 6 miles away." in agencies


def test_border_zip_pulls_the_state_across_the_line(ask, fake):
    """§8.3: south Charlotte is within 15 miles of South Carolina."""
    answer = ask("find_care", kind="nursing home", zip="28273")
    assert answer == "\n".join(
        [
            "Queen City Nursing Center, Charlotte, under a mile away. CMS rates it 3 of 5 "
            "overall. (704) 555 0114.",
            "Fort Mill Place, Fort Mill, about 8 miles away. CMS rates it 5 of 5 overall. "
            "(803) 555 0201.",
            "",
            SOURCE_NH,
            CALL,
        ]
    )
    states = sorted(r.url.params["conditions[0][value]"] for r in fake.data_requests())
    assert states == ["NC", "SC"]


def test_min_rating_excludes_the_unrated(ask):
    """§8.4, both kinds."""
    rated = ask("find_care", kind="nursing home", zip="27502", min_rating=3)
    assert "Cary Oaks" not in rated
    assert "has not rated" not in rated
    for name in ("Apex Ridge Center", "Green Level Health", "Morrisville Gardens"):
        assert name not in rated  # rated below 3
    assert "St. Mary's Care Center" in rated
    assert "There are" not in rated  # 6 within 15 miles rate 3 or more

    unfiltered = ask("find_care", kind="nursing home", zip="27502")
    assert "Cary Oaks Nursing and Rehab, Cary, about 6 miles away. CMS has not rated it " in (
        unfiltered
    )

    agencies = ask("find_care", kind="home health", zip="27502", min_rating=1)
    assert "Holly Springs Home Health" not in agencies
    assert "Apex Home Care" in agencies


def test_none_near_then_the_nearest_within_a_hundred_miles(ask):
    answer = ask("find_care", kind="nursing home", zip="27936")
    assert answer == "\n".join(
        [
            "No nursing homes within 15 miles of 27936 in Medicare's list. The nearest is "
            "Manteo Shores Care in Manteo, about 46 miles away.",
            "",
            SOURCE_NH,
            CALL,
        ]
    )


def test_none_near_and_none_within_a_hundred(ask):
    answer = ask("find_care", kind="home health", zip="27936")
    assert answer == "\n".join(
        [
            "No home health agencies within 15 miles of 27936 in Medicare's list.",
            "",
            SOURCE_HH,
            CALL,
        ]
    )


def test_miles_is_one_to_a_hundred_and_one_mile_is_singular(ask):
    one = ask("find_care", kind="nursing home", zip="27502", miles=0.2)
    assert one.startswith("Apex Ridge Center, Apex, under a mile away.")
    assert "Pine Hollow" not in one  # just over a mile
    far = ask("find_care", kind="nursing home", zip="27936", miles=1)
    assert far.startswith("No nursing homes within 1 mile of 27936 in Medicare's list.")
    wide = ask("find_care", kind="nursing home", zip="27502", miles=5000)
    assert "There are " in wide and "within 100 miles" in wide


def test_refusals_stand_alone(ask, fake):
    assert ask("find_care", kind="hospital", zip="27502") == text.KIND_UNKNOWN
    assert ask("find_care", kind="hospice", zip="27502") == text.KIND_UNKNOWN
    for bad in ("2750", "275021", "27502-1234", "abcde", "", "00000"):
        assert ask("find_care", kind="nursing home", zip=bad) == text.ZIP_UNKNOWN, bad
    assert fake.requests == []  # a refusal reads nothing
