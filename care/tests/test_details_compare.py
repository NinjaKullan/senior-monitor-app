"""care_details and compare_care (spec 021 §3.2, §3.3; acceptance §8.5, §8.6)."""

from __future__ import annotations

import re

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

PINE_HOLLOW = [
    "Pine Hollow Health and Rehabilitation, 101 Holly Rd, Apex, NC 27502, about 1 mile from "
    "27502. (919) 555 0101.",
    "CMS rates it 4 of 5 overall: 3 for health inspections, 4 for staffing, 5 for quality "
    "measures.",
    "120 certified beds. For profit - Corporation.",
]
ST_MARYS = [
    "St. Mary's Care Center, 400 Church St, Cary, NC 27513, about 6 miles from 27502. "
    "(919) 555 0104.",
    "CMS rates it 5 of 5 overall: 5 for health inspections, 5 for staffing, 4 for quality "
    "measures.",
    "150 certified beds. Non profit - Church related.",
]
APEX_HOME_CARE = [
    "Apex Home Care, 10 Salem St, Apex, NC 27502, under a mile from 27502. (919) 555 0301.",
    "CMS rates its quality of patient care 3.5 of 5.",
    "Offers nursing care, physical therapy, occupational therapy, speech pathology, medical "
    "social services, and home health aide.",
    "Voluntary non profit - private. Medicare certified since 1998.",
]
PINE_HOLLOW_DURHAM_HEAD = (
    "Pine Hollow of Durham, 800 Ninth St, Durham, NC 27701, about 19 miles from 27502. "
    "(919) 555 0111."
)
NEAREST_THREE = "Apex Home Care, Apex Ridge Center, and Pine Hollow Health and Rehabilitation"


def details(ask, name: str, zip: str = "27502") -> str:
    return ask("care_details", name=name, zip=zip)


def test_details_is_the_whole_section_4_set(ask):
    assert details(ask, "Pine Hollow Health and Rehabilitation") == "\n".join(
        [*PINE_HOLLOW, "", SOURCE_NH, CALL]
    )
    assert details(ask, "Apex Home Care") == "\n".join([*APEX_HOME_CARE, "", SOURCE_HH, CALL])


def test_details_carries_cms_flags_and_the_not_rated_forms(ask):
    ridge = details(ask, "Apex Ridge Center")
    assert ridge.split("\n")[1:4] == [
        "CMS rates it 2 of 5 overall: 2 for health inspections, 3 for staffing, 1 for quality "
        "measures.",
        "90 certified beds. Non profit - Corporation.",
        text.ABUSE_LINE,
    ]
    gardens = details(ask, "Morrisville Gardens").split("\n")
    assert gardens[3] == text.SPECIAL_FOCUS_LINE
    # "SFF Candidate" is not a Special Focus Facility; the line is CMS's flag only.
    assert text.SPECIAL_FOCUS_LINE not in details(ask, "Western Wake Care")
    # All four ratings null: NOT_RATED_YET. One null: "not rated" in its place.
    assert details(ask, "Cary Oaks").split("\n")[1] == text.NOT_RATED_YET
    assert details(ask, "Holly Springs Manor").split("\n")[1] == (
        "CMS rates it 3 of 5 overall: 3 for health inspections, 2 for staffing, not rated for "
        "quality measures."
    )
    # Home health, unrated, no services, no certification date.
    assert details(ask, "Holly Springs Home Health").split("\n")[1:4] == [
        text.HH_UNRATED,
        text.SERVICES_NONE,
        "Government - state/ county.",
    ]


def test_name_matching_exact_prefix_substring_case_and_punctuation(ask):
    """§8.5."""
    head = PINE_HOLLOW_DURHAM_HEAD
    # Exact beats a nearer prefix match.
    assert details(ask, "PINE HOLLOW OF DURHAM").startswith(head)
    # Prefix: two homes start "Pine Hollow"; the nearer wins the tie.
    assert details(ask, "pine hollow").startswith(PINE_HOLLOW[0])
    # Substring, when nothing starts with it.
    assert details(ask, "hollow of").startswith(head)
    # Punctuation and case ignored, both ways round.
    for asked in ("st marys care center", "St. Mary's", "ST MARYS", "st. mary’s care"):
        assert details(ask, asked).startswith(ST_MARYS[0]), asked
    # A substring that many names share goes to the nearest.
    assert details(ask, "care").startswith(APEX_HOME_CARE[0])


def test_no_match_names_the_three_nearest(ask):
    assert details(ask, "Sunny Acres") == "\n".join(
        [
            f"Medicare's list has nothing near 27502 called Sunny Acres. The nearest names are "
            f"{NEAREST_THREE}.",
            "",
            SOURCE_HH,  # both kinds were read; the older date is said
            CALL,
        ]
    )


def test_matching_is_within_fifty_miles(ask):
    # Biscoe is about 57 miles from Apex and about 34 from Sanford.
    assert details(ask, "Biscoe Valley Care").startswith("Medicare's list has nothing near")
    assert details(ask, "Biscoe Valley Care", zip="27330").startswith("Biscoe Valley Care, ")


def test_details_refusals(ask):
    assert details(ask, "Apex Home Care", zip="275") == text.ZIP_UNKNOWN


def test_compare_needs_two_resolvable_names(ask):
    """§8.6, first half."""
    assert ask("compare_care", names=["Apex Ridge Center", "Sunny Acres"], zip="27502") == (
        text.COMPARE_NEED_TWO
    )
    assert ask("compare_care", names=["Apex Ridge Center"], zip="27502") == text.COMPARE_NEED_TWO
    assert ask("compare_care", names=[], zip="27502") == text.COMPARE_NEED_TWO
    # Two names for one home are one home.
    assert ask("compare_care", names=["Apex Ridge", "apex ridge center"], zip="27502") == (
        text.COMPARE_NEED_TWO
    )


COMPARATIVES = ("best", "better", "worse", "top", "recommend")


def test_compare_three_in_the_callers_order_and_no_winner(ask):
    """§8.6, second half: three paragraphs in order, then COMPARE_CLOSE, and
    never a comparative word."""
    answer = ask(
        "compare_care", names=["St. Mary's", "Apex Home Care", "Pine Hollow Health"], zip="27502"
    )
    paragraphs = answer.split("\n\n")
    assert paragraphs[:4] == [
        "\n".join(ST_MARYS),
        "\n".join(APEX_HOME_CARE),
        "\n".join(PINE_HOLLOW),
        text.COMPARE_CLOSE,
    ]
    # Two datasets in one answer: the older "last updated" is the one said.
    assert paragraphs[4] == "\n".join([SOURCE_HH, CALL])
    for word in COMPARATIVES:
        assert not re.search(rf"\b{word}\b", answer, re.IGNORECASE), word


def test_compare_keeps_an_unresolved_name_in_its_place(ask):
    answer = ask(
        "compare_care", names=["Apex Ridge Center", "Sunny Acres", "St Marys"], zip="27502"
    )
    paragraphs = answer.split("\n\n")
    assert paragraphs[0].startswith("Apex Ridge Center, 250 Ridge View Dr")
    assert paragraphs[1] == (
        f"Medicare's list has nothing near 27502 called Sunny Acres. The nearest names are "
        f"{NEAREST_THREE}."
    )
    assert paragraphs[2] == "\n".join(ST_MARYS)
    assert paragraphs[3] == text.COMPARE_CLOSE


def test_compare_reads_at_most_four(ask):
    names = ["Apex Ridge", "Pine Hollow Health", "St Marys", "Western Wake", "Green Level"]
    answer = ask("compare_care", names=names, zip="27502")
    assert "Green Level" not in answer
    assert answer.count("\n\n") == 4 + 1  # four homes, the close, the footer
