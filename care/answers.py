"""CMS rows into Kettle's sentences (spec 021 §3 and §4). Pure functions.

No I/O here: `app.py` reads CMS and the centroids, this turns what came back
into the words, and the tests hold every sentence character for character.

Names, addresses and cities are title-cased once (CMS shouts). Ratings are
CMS's own numbers, said as "CMS rates it". Nothing here ranks, sums,
averages, or calls anything good or bad; the abuse and special focus lines
are the only warnings and they are CMS's own flags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from care import cms
from care import copy as text
from care.geo import Centroids, miles_between, normalize_zip

NURSING = "nursing"
HOME_HEALTH = "home_health"
DATASET = {NURSING: cms.NURSING_HOMES, HOME_HEALTH: cms.HOME_HEALTH}
KIND_OF = {cms.NURSING_HOMES: NURSING, cms.HOME_HEALTH: HOME_HEALTH}
PLURAL = {NURSING: text.KIND_NURSING_PLURAL, HOME_HEALTH: text.KIND_HOME_HEALTH_PLURAL}

#: §3.1: what `kind` accepts. Anything else is KIND_UNKNOWN.
KINDS = {
    "nursing home": NURSING,
    "nursing homes": NURSING,
    "home health": HOME_HEALTH,
    "home health agency": HOME_HEALTH,
    "home health agencies": HOME_HEALTH,
    "home care": HOME_HEALTH,
}

LIST_CAP = 8
DEFAULT_MILES = 15.0
MAX_MILES = 100.0
MATCH_MILES = 50.0

_SMALL_WORDS = {"of", "and", "the", "at", "in", "on", "for", "a", "an", "to", "by"}
_ROMAN = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii"}
_UNRATED = {"", "-", "not available", "n/a", "na", "none"}


def parse_kind(kind: str | None) -> str | None:
    return KINDS.get(" ".join(str(kind or "").lower().split()))


def title(value: object) -> str:
    """CMS's shouting, title-cased once: small words stay small after the
    first, Roman numerals stay upper, an O' or D' keeps its capital."""
    words = str(value or "").strip().split()
    out = []
    for index, word in enumerate(words):
        lower = word.lower()
        if index > 0 and lower in _SMALL_WORDS:
            out.append(lower)
        elif lower.strip(",.") in _ROMAN:
            out.append(word.upper())
        else:
            parts = lower.split("-")
            out.append("-".join(_cap(part) for part in parts))
    return " ".join(out)


def _cap(word: str) -> str:
    if len(word) > 2 and word[1] == "'":  # o'neil, d'angelo
        return word[0].upper() + "'" + word[2].upper() + word[3:]
    return word[:1].upper() + word[1:]


def sentence_case(value: object) -> str:
    """Ownership as CMS words it, with only its first letter capitalised when
    CMS sent it in capitals (home health does; nursing homes do not)."""
    words = str(value or "").strip()
    if words and words == words.upper():
        words = words.lower()
    return words[:1].upper() + words[1:]


def phone(value: object) -> str:
    """(919) 555 0100, or empty when CMS lists no usable number."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return ""
    return f"({digits[:3]}) {digits[3:6]} {digits[6:]}"


def rating(value: object) -> float | None:
    """A CMS star value as a number, or None when CMS has not rated it."""
    raw = str(value if value is not None else "").strip()
    if raw.lower() in _UNRATED:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def stars(value: float) -> str:
    """4.0 reads 4; 3.5 reads 3.5."""
    return f"{value:g}"


def distance_words(miles: float) -> str:
    """§4: whole miles, 'about'; under one mile reads 'under a mile'."""
    if miles < 1:
        return text.UNDER_A_MILE
    rounded = int(miles + 0.5)
    if rounded == 1:
        return text.DISTANCE_ABOUT_ONE
    return text.DISTANCE_ABOUT.format(miles=rounded)


def one_mile(sentence: str) -> str:
    """The §10 templates say '{miles} miles'; one of them is one mile."""
    return re.sub(r"\b1 miles\b", "1 mile", sentence)


def listing(items: list[str]) -> str:
    """a; a and b; a, b, and c."""
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


# --- a provider, placed ---------------------------------------------------------


@dataclass(frozen=True)
class Placed:
    row: dict[str, Any]
    kind: str
    miles: float

    @property
    def name(self) -> str:
        return title(self.row.get("provider_name"))

    @property
    def city(self) -> str:
        return title(self.row.get("citytown"))

    @property
    def score(self) -> float | None:
        """The rating `min_rating` filters on (§3.1)."""
        key = "overall_rating" if self.kind == NURSING else "quality_of_patient_care_star_rating"
        return rating(self.row.get(key))


def provider_point(
    row: dict[str, Any], kind: str, centroids: Centroids
) -> tuple[float, float] | None:
    """§4: a nursing home by its CMS latitude and longitude, falling back to
    its ZIP's centroid when CMS has none; a home health agency (CMS gives no
    coordinates) by its ZIP's centroid."""
    if kind == NURSING:
        try:
            lat, lon = float(row.get("latitude")), float(row.get("longitude"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            pass
        else:
            return (lat, lon)
    zip5 = normalize_zip(row.get("zip_code"))
    return centroids.point(zip5) if zip5 else None


def place(
    rows: list[dict[str, Any]], here: tuple[float, float], centroids: Centroids
) -> list[Placed]:
    """Every row that can be put on the map, nearest first (name breaks ties)."""
    placed = []
    for row in rows:
        kind = KIND_OF[row["_dataset"]]
        point = provider_point(row, kind, centroids)
        if point is not None:
            placed.append(Placed(row, kind, miles_between(here, point)))
    placed.sort(key=lambda p: (p.miles, p.name))
    return placed


# --- the sentences ----------------------------------------------------------------


def _phone_sentence(row: dict[str, Any]) -> str:
    number = phone(row.get("telephone_number"))
    return f" {number}." if number else ""


def list_sentence(p: Placed) -> str:
    """§4 list sentence (find_care)."""
    score = p.score
    if p.kind == NURSING:
        said = (
            text.NH_LIST_RATED.format(overall=stars(score))
            if score is not None
            else text.NH_LIST_UNRATED
        )
        template = text.NH_LIST
    else:
        said = text.HH_RATED.format(stars=stars(score)) if score is not None else text.HH_UNRATED
        template = text.HH_LIST
    return template.format(
        name=p.name,
        city=p.city,
        distance=distance_words(p.miles),
        rating=said,
        phone_sentence=_phone_sentence(p.row),
    )


def details(p: Placed, asked_zip: str) -> list[str]:
    """§4 details sentence set (care_details, compare_care), one line each."""
    row = p.row
    address_key = "provider_address" if p.kind == NURSING else "address"
    first = text.DETAILS_LINE_1.format(
        name=p.name,
        address=title(row.get(address_key)),
        city=p.city,
        state=str(row.get("state") or "").upper(),
        zip=normalize_zip(row.get("zip_code")) or "",
        distance=distance_words(p.miles),
        asked_zip=asked_zip,
        phone=_phone_sentence(row),
    )
    return [first, *(_nursing_lines(row) if p.kind == NURSING else _home_health_lines(row))]


def _nursing_lines(row: dict[str, Any]) -> list[str]:
    overall = rating(row.get("overall_rating"))
    subs = [
        rating(row.get(k))
        for k in ("health_inspection_rating", "staffing_rating", "qm_rating")
    ]
    if overall is None and all(s is None for s in subs):
        ratings = text.NOT_RATED_YET
    else:

        def word(value: float | None) -> str:
            return stars(value) if value is not None else text.NOT_RATED

        ratings = text.NH_DETAILS_RATINGS.format(
            overall=text.NH_OVERALL.format(overall=stars(overall))
            if overall is not None
            else text.NOT_RATED,
            health=word(subs[0]),
            staffing=word(subs[1]),
            qm=word(subs[2]),
        )
    lines = [ratings]
    third = []
    beds = rating(row.get("number_of_certified_beds"))
    if beds is not None:
        third.append(text.NH_BEDS.format(beds=stars(beds)))
    ownership = sentence_case(row.get("ownership_type"))
    if ownership:
        third.append(f"{ownership}.")
    if third:
        lines.append(" ".join(third))
    if str(row.get("abuse_icon") or "").strip().upper() in {"Y", "YES", "TRUE"}:
        lines.append(text.ABUSE_LINE)
    if str(row.get("special_focus_status") or "").strip().upper() == "SFF":
        lines.append(text.SPECIAL_FOCUS_LINE)
    return lines


def _home_health_lines(row: dict[str, Any]) -> list[str]:
    score = rating(row.get("quality_of_patient_care_star_rating"))
    lines = [text.HH_RATED.format(stars=stars(score)) if score is not None else text.HH_UNRATED]
    offered = [
        word
        for column, word in zip(cms.HH_SERVICE_COLUMNS, text.HH_SERVICE_WORDS, strict=True)
        if str(row.get(column) or "").strip().lower() in {"yes", "y", "true"}
    ]
    lines.append(
        text.HH_SERVICES.format(services=listing(offered)) if offered else text.SERVICES_NONE
    )
    last = []
    ownership = sentence_case(row.get("type_of_ownership"))
    if ownership:
        last.append(f"{ownership}.")
    year = re.search(r"\b(1[89]\d\d|20\d\d)\b", str(row.get("certification_date") or ""))
    if year:
        last.append(text.HH_CERTIFIED.format(year=year.group(1)))
    if last:
        lines.append(" ".join(last))
    return lines


# --- name matching (§3.2) -----------------------------------------------------------


def _norm(value: object) -> str:
    """St. Mary's, st marys and ST MARYS are one name; Fuquay-Varina is two words."""
    dropped = str(value or "").lower().replace("'", "").replace("\u2019", "").replace(".", "")
    kept = "".join(ch if ch.isalnum() else " " for ch in dropped)
    return " ".join(kept.split())


def resolve(asked: str, placed: list[Placed]) -> Placed | None:
    """The one provider whose name matches best: exact, then prefix, then
    substring, case and punctuation ignored; the nearer wins a tie. Only
    providers within MATCH_MILES are candidates. `placed` is nearest first."""
    wanted = _norm(asked)
    if not wanted:
        return None
    near = [p for p in placed if p.miles <= MATCH_MILES]
    for test in (
        lambda n: n == wanted,
        lambda n: n.startswith(wanted),
        lambda n: wanted in n,
    ):
        for p in near:
            if test(_norm(p.row.get("provider_name"))):
                return p
    return None


def nearest_names(placed: list[Placed], count: int = 3) -> str:
    return listing([p.name for p in placed[:count]])


# --- the footer ----------------------------------------------------------------------


def date_words(value: str) -> str:
    """2026-08-01 reads August 1, 2026. Anything else is said as CMS gave it."""
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if not match:
        return value
    year, month, day = (int(g) for g in match.groups())
    return f"{_MONTHS[month - 1]} {day}, {year}"


_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
