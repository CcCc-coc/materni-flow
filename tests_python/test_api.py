# -*- coding: utf-8 -*-

from learn_smb_lending_lens import api


def test_api():
    _ = api.one


if __name__ == "__main__":
    from learn_smb_lending_lens.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_smb_lending_lens.api",
        preview=False,
    )
