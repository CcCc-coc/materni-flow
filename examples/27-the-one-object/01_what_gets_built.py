# -*- coding: utf-8 -*-

"""
Show that `one` builds nothing until something asks for it.

Every expensive thing on the One object is a cached_property, so importing it
costs almost nothing and each piece appears only when first touched. This script
makes that visible: it prints which pieces exist before and after one read.

    .venv/bin/python examples/27-the-one-object/01_what_gets_built.py

Only `config` is touched, on purpose -- reaching for `engine` would open a
database connection and `agent` would need a live API key.
"""

from agent_app.api import one

# cached_property stores its value in the instance __dict__ under its own name,
# so the presence of a name there is exactly "has this been built yet".
WATCHED = ["config", "engine", "remote_postgres_engine", "boto_ses", "model", "agent"]


def snapshot(label: str) -> None:
    print(f"  {label}")
    for name in WATCHED:
        built = name in one.__dict__
        print(f"    {name:26} {'built' if built else '-'}")
    print()


def main() -> None:
    print("A freshly imported `one`:")
    snapshot("(nothing has been asked for yet)")

    print("Now read one.config.schema_name ...")
    value = one.config.schema_name
    print(f"  -> {value!r}\n")
    snapshot("(after touching config)")

    print("Only `config` got built. The database engines, the boto3 session and")
    print("the agent are still absent -- nobody asked, so nobody paid.")
    print()
    print("That is what makes `one` safe to import from anywhere: a test that")
    print("needs the config does not drag a database connection along with it.")


if __name__ == "__main__":
    main()
