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

The bodies are the PM's draft, verbatim. Two things in them are the PM's to
settle before Wave B sends anything, and both are recorded in DECISIONS rather
than quietly edited here:

* They say "her" and "she". DECISIONS 24 is standing policy that nothing infers
  a pronoun from a name, and `ladder_messages.py` carries a neutral clause for
  exactly that reason. The founder's own family includes a father.
* The follow-on carries an em dash, which DECISIONS 127 retired from
  customer-facing *site* copy. Whether that ruling reaches product messages is
  the PM's call.
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
#: and law #6's ladder is that ordering: she hears from Kettle before anyone
#: hears about her.
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
        body="{parent_name}'s morning looked like her morning. Next note this evening.",
        variables=("parent_name",),
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
            "Quiet so far this morning. Kettle will check in with her first if "
            "that continues."
        ),
    ),
    Template(
        # Verbatim from the site, which pins this exact string as its one
        # allowed question about a person: it is addressed *to* her and asks
        # rather than concludes.
        id="ask_parent",
        kind=KIND_ASK,
        audience=AUDIENCE_PARENT,
        body="Everything okay today? Reply whenever suits.",
    ),
    Template(
        # The only message that ever tells a child about a quiet day, and the
        # ladder's handoff: it reports two facts and then stops, because the
        # family knows things Kettle cannot.
        id="follow_on_family",
        kind=KIND_FOLLOW_ON,
        audience=AUDIENCE_CHILD,
        body=(
            "{parent_name}'s usual morning hasn't shown up today, and she hasn't "
            "answered Kettle's note yet. You know her day best — a call from you "
            "beats anything Kettle can send."
        ),
        variables=("parent_name",),
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
    with `{parent_name}` still in it is worse than one that never sent.
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
