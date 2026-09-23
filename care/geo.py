"""Where a ZIP is, how far apart two places are, and which states to read (§5).

Everything here is offline. "Near" is the great-circle distance in statute
miles between the asked ZIP's Census 2020 ZCTA centroid and the provider, and
the centroids ship with the app in `data/zcta.csv`. No geocoding service, no
key, no outbound call: the only host this app ever talks to is CMS.

ZIP to state is the USPS first-three-digits table below, because the Census
centroid file carries no state. A state's reach is the bounding box of its
own centroids, so a Charlotte ZIP asked for 15 miles pulls South Carolina and
an Apex ZIP does not.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "zcta.csv"
EARTH_RADIUS_MILES = 3958.7613

#: USPS three-digit ZIP prefixes by state, as inclusive ranges. Unassigned
#: prefixes and the military ones (AA, AE, AP) are simply absent: a ZIP there
#: has no state CMS lists providers for.
_PREFIX_RANGES: tuple[tuple[int, int, str], ...] = (
    (5, 5, "NY"), (6, 7, "PR"), (8, 8, "VI"), (9, 9, "PR"),
    (10, 27, "MA"), (28, 29, "RI"), (30, 38, "NH"), (39, 49, "ME"),
    (50, 54, "VT"), (55, 55, "MA"), (56, 59, "VT"), (60, 69, "CT"),
    (70, 89, "NJ"), (100, 149, "NY"), (150, 196, "PA"), (197, 199, "DE"),
    (200, 200, "DC"), (201, 201, "VA"), (202, 205, "DC"), (206, 219, "MD"),
    (220, 246, "VA"), (247, 268, "WV"), (270, 289, "NC"), (290, 299, "SC"),
    (300, 319, "GA"), (320, 339, "FL"), (341, 349, "FL"), (350, 369, "AL"),
    (370, 385, "TN"), (386, 397, "MS"), (398, 399, "GA"), (400, 427, "KY"),
    (430, 459, "OH"), (460, 479, "IN"), (480, 499, "MI"), (500, 528, "IA"),
    (530, 549, "WI"), (550, 567, "MN"), (569, 569, "DC"), (570, 577, "SD"),
    (580, 588, "ND"), (590, 599, "MT"), (600, 629, "IL"), (630, 658, "MO"),
    (660, 679, "KS"), (680, 693, "NE"), (700, 714, "LA"), (716, 729, "AR"),
    (730, 732, "OK"), (733, 733, "TX"), (734, 749, "OK"), (750, 799, "TX"),
    (800, 816, "CO"), (820, 831, "WY"), (832, 838, "ID"), (840, 847, "UT"),
    (850, 865, "AZ"), (870, 884, "NM"), (885, 885, "TX"), (889, 898, "NV"),
    (900, 961, "CA"), (967, 968, "HI"), (969, 969, "GU"), (970, 979, "OR"),
    (980, 994, "WA"), (995, 999, "AK"),
)


def state_for(zip5: str) -> str | None:
    """The state a five-digit ZIP belongs to, from its first three digits."""
    if len(zip5) != 5 or not zip5.isdigit():
        return None
    prefix = int(zip5[:3])
    for low, high, state in _PREFIX_RANGES:
        if low <= prefix <= high:
            return state
    return None


def miles_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance in statute miles (haversine)."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_MILES * math.asin(min(1.0, math.sqrt(h)))


@dataclass(frozen=True)
class Box:
    south: float
    west: float
    north: float
    east: float

    def nearest_point(self, point: tuple[float, float]) -> tuple[float, float]:
        lat, lon = point
        return (min(max(lat, self.south), self.north), min(max(lon, self.west), self.east))


class Centroids:
    """The ZCTA centroid table, and each state's bounding box derived from it."""

    def __init__(self, points: dict[str, tuple[float, float]]) -> None:
        self.points = points
        boxes: dict[str, list[float]] = {}
        for zcta, (lat, lon) in points.items():
            state = state_for(zcta)
            if state is None:
                continue
            box = boxes.setdefault(state, [lat, lon, lat, lon])
            box[0], box[1] = min(box[0], lat), min(box[1], lon)
            box[2], box[3] = max(box[2], lat), max(box[3], lon)
        self.boxes = {state: Box(*b) for state, b in boxes.items()}

    @classmethod
    def load(cls, path: Path = DATA) -> Centroids:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            points = {
                row["zcta"]: (float(row["lat"]), float(row["lon"])) for row in reader
            }
        return cls(points)

    def point(self, zip5: str) -> tuple[float, float] | None:
        return self.points.get(zip5)

    def states_within(self, zip5: str, miles: float) -> list[str]:
        """The asked ZIP's own state, then every other state whose centroid
        box comes within `miles` of the asked point, alphabetically."""
        own = state_for(zip5)
        here = self.point(zip5)
        if own is None or here is None:
            return []
        others = sorted(
            state
            for state, box in self.boxes.items()
            if state != own and miles_between(here, box.nearest_point(here)) <= miles
        )
        return [own, *others]


def normalize_zip(value: object) -> str | None:
    """A CMS ZIP field as five digits: ZIP+4 is cut, a dropped leading zero
    is put back. None when there is nothing ZIP-shaped in it."""
    digits = "".join(ch for ch in str(value or "").split("-")[0] if ch.isdigit())
    if not digits or len(digits) > 5:
        return digits[:5] if len(digits) == 9 else None
    return digits.zfill(5)
