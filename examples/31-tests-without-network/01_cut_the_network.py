# -*- coding: utf-8 -*-

"""
Prove the claim: not one test in this repo opens a network connection.

The proof is not "read the tests and take my word for it". It is: break every
outbound socket in the process, then run the whole suite. If anything reached
for the network, it now raises, loudly, with the name of the test attached.

Run it:
    .venv/bin/python examples/31-tests-without-network/01_cut_the_network.py
"""

import socket
import sys

import pytest

from agent_app.paths import path_enum

BLOCKED = []


class NetworkIsCut(RuntimeError):
    """Raised instead of letting a socket reach the outside world."""


def _refuse(self, address, *args, **kwargs):
    """Stand-in for socket.connect. Records the attempt, then refuses it."""
    BLOCKED.append(address)
    raise NetworkIsCut(
        f"a test tried to open a network connection to {address!r}. "
        f"Every test in this repo is supposed to run offline."
    )


# Unix domain sockets and in-process loopback are not "the network", but this
# repo's tests do not need either, so the blanket ban is the honest test.
socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.create_connection = lambda *a, **kw: _refuse(None, a[0] if a else None)

print("network is cut. running the full Python test suite...\n")

exit_code = pytest.main(
    [
        str(path_enum.dir_project_root / "tests_python"),
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
    ]
)

print()
print("=" * 70)
if BLOCKED:
    print(f"FAILED: {len(BLOCKED)} connection attempt(s): {BLOCKED}")
else:
    print("No test attempted a single outbound connection.")
print("=" * 70)
print()
print("This repo talks to PostgreSQL, to AWS and to a large language model.")
print("None of that happened here. How, is what this Task is about:")
print("  - a database   -> reflect an in-memory SQLite, or hand-build the metadata")
print("  - AWS DynamoDB -> moto, a real implementation running inside this process")
print("  - the model    -> replace one.config, then assert on how it was built")

sys.exit(exit_code)
