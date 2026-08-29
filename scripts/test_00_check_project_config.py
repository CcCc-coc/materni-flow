# -*- coding: utf-8 -*-

"""
Preflight check: does this repo still agree with the content in ``data/``?

This is the numbered-script door onto :mod:`agent_app.content_check`, kept so the
setup sequence in ``scripts/`` reads start to finish. Three equivalent ways in::

    .venv/bin/python scripts/test_00_check_project_config.py
    .venv/bin/agent-app check-content
    mise run check-content

All three run the same code. Two doors to one behaviour is fine; two
implementations of it is not, which is why nothing is checked here.

Pass ``--retired`` right after a dataset swap to prove the previous domain's
vocabulary is really gone::

    .venv/bin/python scripts/test_00_check_project_config.py --retired "patient,bed,ward"

What it covers, and the one thing it does not: see the module docstring of
:mod:`agent_app.content_check`. Icon names and required ``site.toml`` keys are
checked by ``mise run build-web``, because only the frontend loader knows them.
"""

import sys

from agent_app.cli import main

if __name__ == "__main__":
    sys.exit(main(["check-content", *sys.argv[1:]]))
