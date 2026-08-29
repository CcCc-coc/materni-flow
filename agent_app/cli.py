# -*- coding: utf-8 -*-

"""
The application's command line: ``agent-app <command>``.

Installed as a console script by ``pyproject.toml``, so ``mise.toml`` names a
command rather than a file path. That indirection is the point: where a check
happens to live can change without every task, doc, and habit changing with it.

**Only application commands belong here.** Building the dataset and publishing it
to PostgreSQL live in the teaching layer's own CLI
(``.claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py``) and
must stay there -- that layer is deleted as a set of directories, and a shared
entry point would leave a broken subcommand behind. The test for a new command is
the same one the rest of the repo uses: is it part of this app, or part of
teaching someone to build it?

Argument parsing only; the work lives in the module each command calls.

    agent-app check-content
    agent-app check-content --retired "patient,bed,ward"
"""

import argparse


def cmd_check_content(args: argparse.Namespace) -> int:
    from agent_app.content_check import run

    retired = [t.strip() for t in args.retired.split(",") if t.strip()]
    return run(retired=retired)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-app",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser(
        "check-content",
        help="verify data/ still agrees with the prompt, the seed, and itself",
    )
    check.add_argument(
        "--retired",
        default="",
        metavar="WORDS",
        help=(
            "Comma-separated vocabulary from the dataset this repo used to "
            "serve. Pass it right after a swap to prove none of it survives, "
            'e.g. --retired "patient,bed,ward". Omitted by default.'
        ),
    )
    check.set_defaults(func=cmd_check_content)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
