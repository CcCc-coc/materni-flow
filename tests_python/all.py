# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from learn_smb_lending_lens.tests import run_cov_test

    run_cov_test(
        __file__,
        "learn_smb_lending_lens",
        is_folder=True,
        preview=False,
    )