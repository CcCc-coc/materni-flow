# -*- coding: utf-8 -*-

import pytest

from agent_app import cli


class TestBuildParser:
    def test_subcommand_is_required(self):
        """Bare `agent-app` must say what it wants, not do something arbitrary."""
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args([])

    def test_retired_defaults_to_empty(self):
        args = cli.build_parser().parse_args(["check-content"])
        assert args.retired == ""

    def test_retired_is_passed_through(self):
        args = cli.build_parser().parse_args(["check-content", "--retired", "widget,part"])
        assert args.retired == "widget,part"


class TestMain:
    def test_dispatches_to_the_checker(self, monkeypatch):
        seen = {}

        def fake_run(retired=None):
            seen["retired"] = retired
            return 0

        monkeypatch.setattr("agent_app.content_check.run", fake_run)
        assert cli.main(["check-content"]) == 0
        assert seen["retired"] == []

    def test_splits_and_strips_retired_words(self, monkeypatch):
        """`--retired "widget, part,, "` is four tokens but two words."""
        seen = {}

        def fake_run(retired=None):
            seen["retired"] = retired
            return 0

        monkeypatch.setattr("agent_app.content_check.run", fake_run)
        cli.main(["check-content", "--retired", "widget, part,, "])
        assert seen["retired"] == ["widget", "part"]

    def test_returns_the_checker_exit_code(self, monkeypatch):
        monkeypatch.setattr("agent_app.content_check.run", lambda retired=None: 1)
        assert cli.main(["check-content"]) == 1


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.cli",
        preview=False,
    )
