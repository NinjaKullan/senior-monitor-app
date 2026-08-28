"""The outbound channel's template registry (spec 007 §2.4, bodies from §5).

Every message Kettle sends is a named template in this one module, and nothing
else composes text. Three reasons, in increasing order of how much they cost to
retrofit:

1. The copy law can be scanned over a registry. `test_outbound_copy.py` walks
   every body here — no alarm vocabulary, no verdict about a person, no counts,
   no signal names, no mechanism — and plants a violation of each to prove the
   scan is load-bearing.
2. The ledger stores a template *id*, never a body, so recording that Kettle
   spoke never becomes a copy of what was said (§2.3).
3. WhatsApp requires business-initiated messages outside a 24-hour session to
   use pre-registered templates (§3, Wave D). A registry maps onto that
   requirement one-to-one; text assembled at the call site does not.

The bodies are the founder-approved set, verbatim from DECISIONS 151 and 161.
Three rulings bind every body here, and the copy-law scan enforces each:

* **`{relationship}`, never a name** (DECISIONS 149). Templates never use a
  parent's given name or a family's own pet name — Kettle cannot know what a
  family calls their elders. The variable renders the label the child picked
  at setup from the standard set (`kettle.provisioning.RELATIONSHIP_LABELS`).
* **Pronouns are never guessed** (DECISIONS 149, closing 24): singular they,
  or the sentence is restructured to need none.
* **No em dashes in any body** (DECISIONS 151, extending 127 to product copy).

The ask carries a universal icon (DECISIONS 150): English plus a 👍 a parent
who reads no English can still act on. Reply intake stays content-blind — the
icon is an affordance, never a parsed answer. The site's quoted ask string is
deliberately not updated in this pass; its quote is illustrative (150).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

#: The five things Kettle can say. A sixth is a spec change, not an edit —
#: the all-clear was exactly that (DECISIONS 157/161, migration 0016).
KIND_DIGEST_MORNING = "digest_morning"
KIND_DIGEST_EVENING = "digest_evening"
KIND_ASK = "ask"
KIND_FOLLOW_ON = "follow_on"
KIND_ALL_CLEAR = "all_clear"

KINDS: tuple[str, ...] = (
    KIND_DIGEST_MORNING,
    KIND_DIGEST_EVENING,
    KIND_ASK,
    KIND_FOLLOW_ON,
    KIND_ALL_CLEAR,
)

#: The email subjects (Wave B, per-parent since the email-polish pass).
#: Family-facing copy, so they live in this module and go through the same
#: scan as every body: the registry's guarantee is that no string a family
#: reads exists anywhere else. An email about one parent carries their
#: relationship label in the subject; anything else (or a parent whose label
#: is not set yet) keeps the plain subject. `EMAIL_SUBJECT` is also the HTML
#: wrapper's footer line, so the two stay one string.
EMAIL_SUBJECT = "A note from Kettle"
EMAIL_SUBJECT_PARENT = "A note about {relationship}'s day"


def subject_for(relationship: str | None) -> str:
    """The subject line for one email, given whose day it is about."""
    if relationship:
        return EMAIL_SUBJECT_PARENT.format(relationship=relationship)
    return EMAIL_SUBJECT

#: Who receives a kind. The ask is the only thing that ever reaches a parent,
#: and law #6's ladder is that ordering: the parent hears from Kettle before
#: anyone hears about them.
AUDIENCE_PARENT = "parent"
AUDIENCE_CHILD = "child"


@dataclass(frozen=True)
class Template:
    """One registered message. `id` is what the ledger keeps."""

    id: str
    kind: str
    audience: str
    body: str
    variables: tuple[str, ...] = ()


_REGISTRY: tuple[Template, ...] = (
    Template(
        id="digest_morning_normal",
        kind=KIND_DIGEST_MORNING,
        audience=AUDIENCE_CHILD,
        body="{relationship}'s morning looked like a normal morning. Next note this evening.",
        variables=("relationship",),
    ),
    Template(
        id="digest_evening_normal",
        kind=KIND_DIGEST_EVENING,
        audience=AUDIENCE_CHILD,
        body="A normal day, start to finish. Next note in the morning.",
    ),
    Template(
        # The recovered day (email-polish pass): the morning was quiet at the
        # digest slot — the same condition that chose digest_morning_quiet and
        # armed the ask — but routine pings resumed later and the day ends
        # normal. "Start to finish" would be false for this day; this body
        # tells the same day's true story. Chosen at the evening slot by
        # _due_for_parent; every withhold rule (164's followed-up skip, the
        # evidence gate) is unchanged around it.
        id="digest_evening_recovered",
        kind=KIND_DIGEST_EVENING,
        audience=AUDIENCE_CHILD,
        body="A quiet start, then a normal day. Next note in the morning.",
    ),
    Template(
        # Sent only when the digest time lands before the ask threshold on a day
        # that is quiet so far — which in v1 it always does (08:30 against
        # 11:00). It reports the absence and says what happens next; it does not
        # interpret the absence, which is the no-inference law at the sentence.
        id="digest_morning_quiet",
        kind=KIND_DIGEST_MORNING,
        audience=AUDIENCE_CHILD,
        body=(
            "Quiet so far this morning. Kettle will check in with {relationship} "
            "first if that continues."
        ),
        variables=("relationship",),
    ),
    Template(
        # The one question the product asks about a person, addressed *to* the
        # parent: it asks rather than concludes, which is why it survives the
        # verdict ban. The 👍 is DECISIONS 150's universal icon — an affordance
        # a parent who reads no English can act on, never a parsed answer.
        # The site's older quote of this string is illustrative, not binding.
        id="ask_parent",
        kind=KIND_ASK,
        audience=AUDIENCE_PARENT,
        body="Everything okay today? Reply with a 👍 whenever suits.",
    ),
    Template(
        # The changed-morning follow-on (DECISIONS 151 body 5): signals still
        # arriving, routine absent. The ladder's handoff — it reports two facts
        # and then stops, because the family knows things Kettle cannot. When
        # the phone has stopped reporting entirely, `follow_on_unreachable`
        # renders instead; the two never both send for the same day.
        id="follow_on_family",
        kind=KIND_FOLLOW_ON,
        audience=AUDIENCE_CHILD,
        body=(
            "{relationship}'s usual morning hasn't shown up today, and they "
            "haven't answered Kettle's note yet. You know their day best. "
            "A call from you beats anything Kettle can send."
        ),
        variables=("relationship",),
    ),
    Template(
        # The unreachable-phone follow-on (DECISIONS 161 body 7, the 157
        # mechanism_ok distinction): zero pings of ANY grade all day, so the
        # honest report is about the phone, not the morning. A dead battery
        # must not read as a changed morning.
        id="follow_on_unreachable",
        kind=KIND_FOLLOW_ON,
        audience=AUDIENCE_CHILD,
        body=(
            "{relationship}'s phone has been silent today, which is different "
            "from a quiet morning. A phone that is off or out of battery looks "
            "exactly like this. A call from you settles it either way."
        ),
        variables=("relationship",),
    ),
    Template(
        # The all-clear (DECISIONS 161 body 6): only ever after a follow-on has
        # gone out, when the parent's routine resumes. Once per day, and the
        # ledger row is the resolution record.
        id="all_clear_family",
        kind=KIND_ALL_CLEAR,
        audience=AUDIENCE_CHILD,
        body=(
            "The shape of {relationship}'s usual day is back. Kettle returns "
            "to its twice-a-day notes."
        ),
        variables=("relationship",),
    ),
)

TEMPLATES: dict[str, Template] = {t.id: t for t in _REGISTRY}


def template(template_id: str) -> Template:
    """Look one up, or fail loudly — an unknown id is a bug, not a fallback."""
    try:
        return TEMPLATES[template_id]
    except KeyError:  # pragma: no cover - defensive
        raise KeyError(f"no such template: {template_id}") from None


def render(template_id: str, variables: Mapping[str, str] | None = None) -> str:
    """Fill a template's variables. Every variable it declares must be given.

    No partial renders and no silent blanks: a message that reaches a family
    with `{relationship}` still in it is worse than one that never sent.
    """
    found = template(template_id)
    values = dict(variables or {})
    missing = [name for name in found.variables if not values.get(name)]
    if missing:
        raise ValueError(f"{template_id} needs {', '.join(missing)}")
    extra = set(values) - set(found.variables)
    if extra:
        raise ValueError(f"{template_id} takes no {', '.join(sorted(extra))}")
    return found.body.format(**values)
