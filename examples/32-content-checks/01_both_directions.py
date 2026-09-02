# -*- coding: utf-8 -*-

"""
Show why the kickstart check has to run in BOTH directions.

`render` is what the button promises the reader (which icon it draws). The
trigger phrase inside `action` is what actually makes the model emit that kind
of block. Either one can be wrong while the other looks fine, so checking one
of them catches only half the mistakes.

Nothing here touches data/site.toml. Every question below is made up, and it is
fed to the same function the real check uses.

Run it:
    .venv/bin/python examples/32-content-checks/01_both_directions.py
"""

from agent_app.content_check import kind_from_phrases, RENDER_PHRASES, RENDER_QUOTAS

CASES = [
    (
        "both halves agree",
        "table",
        "Score the current book by risk grade as a Markdown table, and show the SQL.",
    ),
    (
        "the badge promises a chart, the wording asks for prose",
        "chart",
        "Which risk grade is mispriced, and by how much?",
    ),
    (
        "the badge promises nothing, but the wording will draw a flowchart",
        "free",
        "Walk me through what happens to an application, as a flowchart.",
    ),
    (
        "a table question that forgot the second phrase",
        "table",
        "List the ten largest exposures as a Markdown table.",
    ),
    (
        "the wording drifted to a synonym the contract does not list",
        "chart",
        "Show default rate by grade as a bar graph.",
    ),
]

print("=" * 78)
print("What the wording actually produces, vs what the badge promises")
print("=" * 78)
print()

for label, declared, action in CASES:
    actual = kind_from_phrases(action.lower())
    verdict = "agree" if actual == declared else "MISMATCH"
    print(f"  {label}")
    print(f"      action    {action}")
    print(f"      render    {declared!r}   wording produces {actual!r}   -> {verdict}")
    print()

print("=" * 78)
print("The literal phrases the contract recognises")
print("=" * 78)
print()
for kind, groups in RENDER_PHRASES.items():
    for group in groups:
        joined = " / ".join(repr(p) for p in group)
        print(f"  {kind:10s} needs one of  {joined}")
print(f"  {'free':10s} needs NONE of the phrases above")
print()
print("  Note `table` needs a phrase from BOTH of its groups: the table itself")
print("  and the SQL under it. A question with only the first one is not a")
print("  table question by this contract.")
print()

print("=" * 78)
print("The other half of the check: how many of each")
print("=" * 78)
print()
for kind, want in RENDER_QUOTAS.items():
    print(f"  exactly {want} questions of kind {kind!r}")
print()
print("  Twelve questions that all return prose would leave the diagram")
print("  renderer and the chart renderer with nothing to draw, which is the")
print("  same as never having built them.")
