"""A failed build must leave nothing behind (DECISIONS 139).

`vite build` empties its own output directory — but only if it runs. When the
`tsc --noEmit` ahead of it fails, vite never starts, the previous `dist/` is
still sitting there, and every verification step that reads `dist/` passes
against the *last* successful build. That is not theoretical: a planted
regression sailed through `check-prerender.mjs` for exactly this reason while
DECISIONS 136 was being drilled, and the check reported the page was fine.

So both front-end builds clear their output before anything else can fail.
Asserted here, next to the other cross-tree contracts, because the property is
about the pipeline rather than about either package's code.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

#: package directory -> the output directories its build must clear first.
BUILDS = {
    "site": ("dist", "dist-ssr"),
    "webapp": ("dist",),
}


@pytest.mark.parametrize("package", sorted(BUILDS))
def test_the_build_clears_its_output_before_anything_can_fail(package: str):
    scripts = json.loads((ROOT / package / "package.json").read_text())["scripts"]
    build = scripts["build"]
    first, _, rest = build.partition("&&")
    first = first.strip()

    assert first.startswith("rm -rf "), (
        f"{package}'s build must remove its output first, not {first!r} — "
        "otherwise a build that dies leaves a stale artifact for verification "
        "to pass against"
    )
    removed = set(first.removeprefix("rm -rf ").split())
    assert removed == set(BUILDS[package]), f"{package} removes {removed}"
    # And the removal is genuinely first: nothing runs ahead of it that could
    # fail and skip it.
    assert rest.strip(), f"{package}'s build does nothing but delete"


@pytest.mark.parametrize("package", sorted(BUILDS))
def test_verification_runs_after_the_build_and_not_instead_of_it(package: str):
    """The other half: `npm run ci` must build before it verifies."""
    scripts = json.loads((ROOT / package / "package.json").read_text())["scripts"]
    ci = scripts["ci"]
    assert "npm run build" in ci
    assert "npm run verify:build" in ci
    assert ci.index("npm run build") < ci.index("npm run verify:build")
