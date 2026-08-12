# -*- coding: utf-8 -*-

from learn_smb_lending_lens.one.one_00_main import one


class TestConfigMixin:
    def test_config(self):
        _ = one.config


if __name__ == "__main__":
    from learn_smb_lending_lens.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_smb_lending_lens.one.one_01_config",
        preview=False,
    )
