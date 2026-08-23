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

The bodies are the founder-approved set, verbatim from DECISIONS 151. Three
rulings bind every body here, and the copy-law scan enforces each:

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

#: The four things Kettle can say. A fifth is a spec change, not an edit.
KIND_DIGEST_MORNING = "digest_morning"
KIND_DIGEST_EVENING = "digest_evening"
KIND_ASK = "ask"
KIND_FOLLOW_ON = "follow_on"

KINDS: tuple[str, ...] = (KIND_DIGEST_MORNING, KIND_DIGEST_EVENING, KIND_ASK, KIND_FOLLOW_ON)

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
        body="An ordinary day, start to finish. Next note in the morning.",
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
        # The only message that ever tells a child about a quiet day, and the
        # ladder's handoff: it reports two facts and then stops, because the
        # family knows things Kettle cannot.
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
