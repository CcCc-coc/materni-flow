# -*- coding: utf-8 -*-

"""
Show WHEN a bad configuration value complains, and when it stays quiet.

Every Config below is built by hand, so this script needs no .env, no API key,
no database and no network. It runs the same `__post_init__` and `validate()`
the real app runs, which is the point: the checks live on the dataclass, so a
hand-built Config behaves exactly like one built from the environment.

Run it:
    .venv/bin/python examples/30-configuration/01_when_does_it_complain.py
"""

from agent_app.config import Config, get_env, PLACEHOLDER


def show(label: str, build):
    """Build a Config and report whether it survived construction."""
    try:
        cfg = build()
    except ValueError as e:
        print(f"  {label}\n      RAISED  {e}\n")
        return None
    print(f"  {label}\n      ok      llm_provider={cfg.llm_provider!r} model_id={cfg.model_id!r}\n")
    return cfg


print("=" * 78)
print("1. __post_init__ runs at CONSTRUCTION, so these fail before any query")
print("=" * 78)

show(
    "a legal schema name",
    lambda: Config(schema_name="acme_widgets", llm_provider="openai"),
)
show(
    "a schema name starting with a digit",
    lambda: Config(schema_name="9acme", llm_provider="openai"),
)
show(
    "a schema name with a hyphen",
    lambda: Config(schema_name="acme-widgets", llm_provider="openai"),
)
show(
    "a provider nobody implements",
    lambda: Config(schema_name="acme_widgets", llm_provider="skynet"),
)
show(
    "the spend cap turned on without naming a table",
    lambda: Config(schema_name="acme_widgets", llm_provider="openai", quota_enabled=True),
)

print("=" * 78)
print("2. __post_init__ also NORMALIZES, so callers never do it themselves")
print("=" * 78)

show(
    "provider written with stray case and spaces",
    lambda: Config(schema_name="acme_widgets", llm_provider="  OpenAI  "),
)
show(
    "no model_id given, so the provider's default is filled in",
    lambda: Config(schema_name="acme_widgets", llm_provider="anthropic"),
)

print("=" * 78)
print("3. validate() is a SEPARATE, LATER check: credentials")
print("=" * 78)
print("   Construction cannot check these, because a Config is legal without")
print("   them. The app calls validate() when it builds the model.\n")

cfg = Config(schema_name="acme_widgets", llm_provider="openai", openai_api_key=None)
print("   built a Config with no OpenAI key: construction was fine")
try:
    cfg.validate()
    print("   validate() passed (unexpected)\n")
except ValueError as e:
    print(f"   validate() RAISED  {e}\n")

cfg = Config(schema_name="acme_widgets", llm_provider="openai", openai_api_key="sk-fake")
cfg.validate()
print("   with a key present, validate() passes\n")

print("=" * 78)
print("4. The placeholder in .env.example counts as NOT SET")
print("=" * 78)

import os

os.environ["DEMO_VALUE"] = PLACEHOLDER
print(f"   os.environ['DEMO_VALUE'] is {PLACEHOLDER!r}, which is set and non-empty")
print(f"   but get_env('DEMO_VALUE') returns {get_env('DEMO_VALUE')!r}")
print()
print("   That is why a line copied out of .env.example and left uncommented")
print("   does not shadow a real credential somewhere else.")
del os.environ["DEMO_VALUE"]
