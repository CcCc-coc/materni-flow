# -*- coding: utf-8 -*-

"""
Ask the project which database file it is serving, and print the answer.

This is the discovery function from section 7, on its own with nothing else
around it. Run it after gen-data:

    .venv/bin/python examples/14-what-a-dataset-is/01_find_the_seed.py

It has three possible outcomes, and all three are worth seeing:

- exactly one .sqlite in dataset/  -> it prints the path
- none                            -> it refuses, and names the command to build one
- several                         -> it refuses, because picking one silently is
                                     how the wrong dataset gets served
"""

from agent_app.dataset import DIR_DATASET, dataset_sqlite_files, path_dataset_sqlite


def main() -> None:
    found = dataset_sqlite_files()
    print(f"Looking in: {DIR_DATASET}")
    print(f"Files matching *.sqlite: {len(found)}")
    for path in found:
        print(f"  - {path.name}")
    print()

    # path_dataset_sqlite() is what the rest of the project calls. Unlike the
    # listing above it insists on exactly one, so this is the line that raises.
    chosen = path_dataset_sqlite()
    print(f"Serving: {chosen.name} ({chosen.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
