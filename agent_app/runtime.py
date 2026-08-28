# -*- coding: utf-8 -*-

"""
Where am I running?

One question, answered in one place, so that no other module ever reads the
environment to find out:

    from .runtime import runtime

    if runtime.is_local():
        ...

Today the only caller is ``config.py``, which uses the answer to pick
a ``Config`` factory. That is the intended shape: the detection lives here, the
consequences live in the config. Adding a deployment target (AWS Lambda, say)
means adding an ``is_*`` method here and a factory there -- and nothing else in
the codebase learns about it.
"""

import os

from functools import cached_property


class Runtime:
    """Singleton-style runtime detector. Use the ``runtime`` instance, not this class."""

    @cached_property
    def _is_vercel(self) -> bool:
        # See https://vercel.com/docs/environment-variables/system-environment-variables
        return os.environ.get("VERCEL") == "1"

    def is_local(self) -> bool:
        return not self._is_vercel

    def is_vercel(self) -> bool:
        return self._is_vercel


runtime = Runtime()
