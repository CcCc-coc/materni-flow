# -*- coding: utf-8 -*-

"""
Check the rendering contract in all three places at once, and show what each
one alone would fail to notice.

The three halves live in three different languages and three different files:

    data/system-prompt.md            tells the model when to emit a block
    data/site.toml                   the twelve buttons, and what each promises
    components/chat/blocks/index.ts  which fence tags the UI can actually draw

Nothing in the build makes them agree. This script reads all three and lines
them up.

Reads files only. Needs no credentials, no database and no network.

Run it:
    .venv/bin/python examples/34-the-rendering-contract/01_check_all_three_halves.py
"""

import re
import tomllib

from agent_app.content_check import kind_from_phrases, RENDER_QUOTAS
from agent_app.paths import path_enum

ROOT = path_enum.dir_project_root
PROMPT = path_enum.path_bi_agent_system_prompt_md.read_text(encoding="utf-8")
SITE = tomllib.loads(path_enum.path_site_toml.read_text(encoding="utf-8"))
LOOKUP = (ROOT / "components" / "chat" / "blocks" / "index.ts").read_text(encoding="utf-8")

# --- half three: which fence tags does the UI know how to draw? ---------------
table_body = LOOKUP.split("BLOCK_RENDERERS", 1)[1].split("}", 1)[0]
ui_tags = set(re.findall(r"^\s*(\w+):", table_body, re.M))

print("=" * 78)
print("HALF 3  the UI lookup table (components/chat/blocks/index.ts)")
print("=" * 78)
print(f"\n   fence tags with a renderer: {sorted(ui_tags)}")
print("   everything else falls through to plain code\n")

# --- half one: which phrases does the prompt promise to react to? ------------
trigger_section = PROMPT.split("## Rendering Triggers", 1)[1].split("\n## ", 1)[0]
# Only the short quoted phrases in the table itself; the prose below it
# quotes a whole example sentence, which is not a trigger.
quoted = {
    p for p in re.findall(r'"([^"\n]+)"', trigger_section) if len(p) < 40
}

print("=" * 78)
print("HALF 1  the prompt's trigger table (data/system-prompt.md)")
print("=" * 78)
print()
for phrase in sorted(quoted):
    print(f"   the model reacts to  {phrase!r}")
print()

# --- half two: what do the twelve buttons declare and what do they say? ------
actions = SITE["chat"]["suggestedActions"]
tally = {kind: 0 for kind in RENDER_QUOTAS}
mismatch = []
for i, item in enumerate(actions):
    declared = item["render"]
    produced = kind_from_phrases(item["action"].lower())
    tally[declared] = tally.get(declared, 0) + 1
    if declared != produced:
        mismatch.append((i, item["title"], declared, produced))

print("=" * 78)
print("HALF 2  the twelve buttons (data/site.toml)")
print("=" * 78)
print()
for kind, want in RENDER_QUOTAS.items():
    got = tally.get(kind, 0)
    print(f"   {kind:10s} declared {got}, contract wants {want}   "
          f"{'ok' if got == want else 'MISMATCH'}")
print()
if mismatch:
    for i, title, declared, produced in mismatch:
        print(f"   MISMATCH  [{i}] {title}: says {declared!r}, wording produces {produced!r}")
else:
    print("   every button's badge matches what its own wording will produce")
print()

# --- do the halves line up with each other? ----------------------------------
print("=" * 78)
print("Do the three line up?")
print("=" * 78)
print()

# A block kind is only real if the prompt asks for it AND the UI can draw it.
needs_ui = {"flowchart": "mermaid", "chart": "chart"}
for kind, tag in needs_ui.items():
    in_prompt = any(kind_from_phrases(p) == kind for p in quoted)
    in_ui = tag in ui_tags
    used = tally.get(kind, 0)
    verdict = "ok" if (in_prompt and in_ui and used) else "BROKEN"
    print(f"   {kind:10s} prompt={in_prompt!s:5s} ui={in_ui!s:5s} "
          f"buttons={used}   -> {verdict}")
print()

print("=" * 78)
print("What each half alone would MISS")
print("=" * 78)
print()
print("   only the UI table       a renderer nothing ever produces. Zero test")
print("                           failures, zero visible symptoms, dead code.")
print()
print("   only the prompt         the model emits ```chart, the UI has no entry")
print("                           for it, so the reader sees raw JSON.")
print()
print("   only the buttons        the badge draws a chart icon over a paragraph")
print("                           of prose, or draws nothing over a real chart.")
print()
print("   None of those three raises anything. That is why this contract needs")
print("   a check of its own, and why the check reads all three files.")
