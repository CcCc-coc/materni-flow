# -*- coding: utf-8 -*-

"""
The teaching layer's command line: build the dataset, publish it, check it.

**Not a mise task, on purpose.** ``mise.toml`` runs the application -- install,
dev server, tests, checks. None of what this file does is the application: the
agent reads PostgreSQL and does not care how the rows arrived. Keeping these
commands here, next to the skill that explains them, means the teaching layer is
a set of directories you delete rather than lines you have to pick out of a
shared config.

Everything it does lives in ``agent_app/dataset.py``; this is only the argument
parsing. ``agent_app`` is installed into the venv, so this runs from anywhere:

    .venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py gen-data
    ... gen-data --force        # rebuild even though a database is already there
    ... sync-db                 # publish it into this project's PostgreSQL schema
    ... verify-db               # confirm remote matches local, table by table
"""

import sys
import pathlib
import argparse
import importlib


def cmd_gen_data(args: argparse.Namespace) -> int:
    from agent_app.dataset import generate_dataset

    generate_dataset(force=args.force)
    return 0


def _sibling(module: str):
    """
    Import one of the numbered scripts sitting next to this file.

    They already print what a reader wants to see and return a shell exit code,
    so the CLI reuses them whole. Two doors to one behaviour is fine; two
    implementations of it is not.

    They live here rather than in the repo's top-level ``scripts/`` because they
    are teaching material: publishing deletes this directory, and a step that
    builds and publishes the dataset has no business surviving that. Numbered
    from 01 because this is their own sequence now, not a continuation of one
    that lives somewhere else.

    ``sys.path`` is touched explicitly rather than relying on the running
    script's directory, so importing this module from elsewhere works too.
    """
    here = str(pathlib.Path(__file__).absolute().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    return importlib.import_module(module).main


def cmd_sync_db(args: argparse.Namespace) -> int:
    _sibling("01_sync_data_to_remote_db")()
    return 0


def cmd_verify_db(args: argparse.Namespace) -> int:
    return _sibling("02_verify_remote_data")()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teaching_cli.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen-data", help="build dataset/<name>.sqlite from its generator")
    gen.add_argument(
        "--force",
        action="store_true",
        help=(
            "rebuild even if a database exists. Deletes every .sqlite in "
            "dataset/ first, so a leftover from a previous dataset cannot make "
            "discovery ambiguous."
        ),
    )
    gen.set_defaults(func=cmd_gen_data)

    sync = sub.add_parser("sync-db", help="publish the dataset into PostgreSQL")
    sync.set_defaults(func=cmd_sync_db)

    verify = sub.add_parser("verify-db", help="compare remote row counts against local")
    verify.set_defaults(func=cmd_verify_db)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
