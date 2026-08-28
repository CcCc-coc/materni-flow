# -*- coding: utf-8 -*-

"""
Tests for the dataset authoring layer.

**Nothing here touches PostgreSQL, and nothing here runs the generator.** The
generator takes minutes and writes a 7 MB file; a unit test that ran it would be
testing Faker. What is worth testing is everything around it: which file gets
picked, what gets refused, and how a SQLite schema is translated on its way out.

The module under test is itself teaching material and is meant to be deleted
along with ``dataset/``. These tests go with it.
"""

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from agent_app import dataset


@pytest.fixture
def dataset_dir(tmp_path, monkeypatch):
    """Point the module's discovery at a scratch directory."""
    monkeypatch.setattr(dataset, "DIR_DATASET", tmp_path)
    return tmp_path


class TestSqliteDiscovery:
    """
    The database's filename belongs to the dataset, so it is discovered rather
    than named. Every way that can go wrong has to say what to do about it: the
    person reading the message is mid-setup.
    """

    def test_finds_the_one_file(self, dataset_dir):
        (dataset_dir / "acme_widgets.sqlite").touch()
        assert dataset.path_dataset_sqlite().name == "acme_widgets.sqlite"

    def test_the_name_does_not_matter(self, dataset_dir):
        """That is the point: naming it here would make a swap edit agent_app/."""
        (dataset_dir / "something_else.sqlite").touch()
        assert dataset.path_dataset_sqlite().stem == "something_else"

    def test_missing_says_how_to_build_one(self, dataset_dir):
        with pytest.raises(FileNotFoundError, match="gen-data"):
            dataset.path_dataset_sqlite()

    def test_several_files_is_refused_not_guessed(self, dataset_dir):
        """Picking one silently is how the wrong dataset gets served."""
        (dataset_dir / "a.sqlite").touch()
        (dataset_dir / "b.sqlite").touch()
        with pytest.raises(RuntimeError, match="a.sqlite, b.sqlite"):
            dataset.path_dataset_sqlite()

    def test_other_files_are_ignored(self, dataset_dir):
        """The directory also holds the source documents and the generator."""
        (dataset_dir / "00-summary.md").touch()
        (dataset_dir / "04-x_data_generator-cn.py").touch()
        (dataset_dir / "data").mkdir()
        (dataset_dir / "acme.sqlite").touch()
        assert dataset.path_dataset_sqlite().name == "acme.sqlite"

    def test_not_cached(self, dataset_dir):
        """
        A student hits the missing-file error, runs the generator, and retries in
        the same process. A cached miss would survive the fix.
        """
        with pytest.raises(FileNotFoundError):
            dataset.path_dataset_sqlite()
        (dataset_dir / "acme.sqlite").touch()
        assert dataset.path_dataset_sqlite().name == "acme.sqlite"

    def test_listing_does_not_judge(self, dataset_dir):
        """
        ``dataset_sqlite_files`` is the non-raising look. A caller about to
        *build* the database has to be able to check first.
        """
        assert dataset.dataset_sqlite_files() == []
        (dataset_dir / "a.sqlite").touch()
        (dataset_dir / "b.sqlite").touch()
        assert [p.name for p in dataset.dataset_sqlite_files()] == ["a.sqlite", "b.sqlite"]


class TestGeneratorDiscovery:
    def test_finds_the_generator(self, dataset_dir):
        (dataset_dir / "04-acme_data_generator-cn.py").touch()
        assert dataset.path_dataset_generator().name == "04-acme_data_generator-cn.py"

    def test_the_sqlite_is_not_mistaken_for_it(self, dataset_dir):
        (dataset_dir / "acme.sqlite").touch()
        (dataset_dir / "04-acme_data_generator-cn.py").touch()
        assert dataset.path_dataset_generator().suffix == ".py"

    def test_missing_generator_is_named(self, dataset_dir):
        with pytest.raises(FileNotFoundError, match="dataset generator"):
            dataset.path_dataset_generator()


class TestRequirements:
    def test_found_by_fixed_name(self, dataset_dir):
        """Ours, not the dataset's, so it is named rather than discovered."""
        (dataset_dir / "requirements.txt").write_text("Faker\n")
        assert dataset.path_dataset_requirements().name == "requirements.txt"

    def test_missing_says_what_it_is_for(self, dataset_dir):
        with pytest.raises(FileNotFoundError, match="generator"):
            dataset.path_dataset_requirements()


class TestTableInsertOrder:
    def test_parents_come_before_children(self):
        metadata = sa.MetaData()
        sa.Table("part", metadata, sa.Column("id", sa.Integer, primary_key=True))
        sa.Table(
            "widget",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("part_id", sa.Integer, sa.ForeignKey("part.id")),
        )
        assert dataset.table_insert_order(metadata) == ["part", "widget"]

    def test_a_cycle_raises(self):
        """
        No insert order can satisfy a cycle. SQLAlchemy only *warns* and returns
        a list with those constraints ignored -- which would sync fine and then
        fail on the first insert -- so the warning is promoted to an error.
        """
        metadata = sa.MetaData()
        sa.Table(
            "a",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("b_id", sa.Integer, sa.ForeignKey("b.id")),
        )
        sa.Table(
            "b",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("a_id", sa.Integer, sa.ForeignKey("a.id")),
        )
        with pytest.raises(RuntimeError, match="cycle"):
            dataset.table_insert_order(metadata)


class TestToPostgresType:
    """
    SQLite's type affinity is loose, so reflection hands back spellings that
    either do not exist in PostgreSQL or behave differently there. Getting one
    of these wrong does not raise -- it creates a column of the wrong type and
    the data lands mangled.
    """

    @pytest.mark.parametrize(
        "sqlite_type, expected",
        [
            (sa.DATETIME(), sa.TIMESTAMP),
            (sa.DATE(), sa.Date),
            (sa.DECIMAL(12, 2), sa.Numeric),
            (sa.NUMERIC(10, 4), sa.Numeric),
            (sa.BOOLEAN(), sa.Boolean),
            (sa.TEXT(), sa.Text),
            (sa.INTEGER(), sa.Integer),
            (sa.REAL(), sa.Float),
            (sa.FLOAT(), sa.Float),
            (sa.BLOB(), sa.LargeBinary),
        ],
    )
    def test_mapping(self, sqlite_type, expected):
        assert isinstance(dataset.to_postgres_type(sqlite_type), expected)

    def test_varchar_becomes_text(self):
        """
        PostgreSQL TEXT performs identically, and this drops a length limit
        SQLite never enforced -- so a row that fit locally cannot fail remotely.
        """
        assert isinstance(dataset.to_postgres_type(sa.VARCHAR(50)), sa.Text)

    def test_datetime_wins_over_date(self):
        """Both spellings contain "DATE"; order of the checks is load-bearing."""
        assert isinstance(dataset.to_postgres_type(sa.DATETIME()), sa.TIMESTAMP)

    def test_an_unknown_type_is_passed_through(self):
        """A type with no rule is handed on untouched rather than guessed at."""
        unknown = pg.INET()
        assert dataset.to_postgres_type(unknown) is unknown


class TestBuildRemoteMetadata:
    """
    Building the remote schema is pure metadata work -- no connection involved --
    so the whole translation can be checked offline.
    """

    @pytest.fixture
    def local(self):
        metadata = sa.MetaData()
        sa.Table(
            "part",
            metadata,
            sa.Column("id", sa.INTEGER(), primary_key=True),
            sa.Column("part_name", sa.VARCHAR(64), nullable=False),
        )
        sa.Table(
            "widget",
            metadata,
            sa.Column("id", sa.INTEGER(), primary_key=True),
            sa.Column("part_id", sa.INTEGER(), sa.ForeignKey("part.id")),
            sa.Column("price", sa.DECIMAL(12, 2)),
        )
        return metadata

    def test_table_names_are_unchanged(self, local):
        """
        The whole point of using a schema instead of a prefix: the name the
        agent sees must not depend on which engine is behind it.
        """
        remote = dataset.build_remote_metadata(local, "acme_widgets")
        assert sorted(t.name for t in remote.tables.values()) == ["part", "widget"]

    def test_everything_lands_in_the_schema(self, local):
        remote = dataset.build_remote_metadata(local, "acme_widgets")
        assert set(remote.tables) == {"acme_widgets.part", "acme_widgets.widget"}
        assert all(t.schema == "acme_widgets" for t in remote.tables.values())

    def test_foreign_keys_are_repointed_into_the_schema(self, local):
        """
        Left alone they would point at an unqualified ``part.id``, which on the
        remote server means whatever ``search_path`` happens to resolve -- very
        possibly another project's table.
        """
        remote = dataset.build_remote_metadata(local, "acme_widgets")
        widget = remote.tables["acme_widgets.widget"]
        # target_fullname, not str(fk.column): the latter renders unqualified
        # and would pass even if the repointing had not happened.
        targets = [fk.target_fullname for fk in widget.c.part_id.foreign_keys]
        assert targets == ["acme_widgets.part.id"]
        assert all(
            fk.column.table.schema == "acme_widgets"
            for fk in widget.c.part_id.foreign_keys
        )

    def test_types_are_translated(self, local):
        remote = dataset.build_remote_metadata(local, "acme_widgets")
        widget = remote.tables["acme_widgets.widget"]
        part = remote.tables["acme_widgets.part"]
        assert isinstance(part.c.part_name.type, sa.Text)
        assert isinstance(widget.c.price.type, sa.Numeric)

    def test_primary_keys_survive(self, local):
        remote = dataset.build_remote_metadata(local, "acme_widgets")
        assert [c.name for c in remote.tables["acme_widgets.part"].primary_key] == ["id"]

    def test_the_local_metadata_is_not_mutated(self, local):
        """The source is reflected from a file someone may still be reading."""
        dataset.build_remote_metadata(local, "acme_widgets")
        assert local.tables["part"].schema is None
        assert isinstance(local.tables["part"].c.part_name.type, sa.VARCHAR)


class TestNotOnTheProductionPath:
    def test_the_app_does_not_import_the_authoring_layer(self):
        """
        This module is meant to be deleted with the teaching material. Nothing
        the API serves a request through may depend on it, or deleting it takes
        the app down.
        """
        import ast
        import pathlib

        root = pathlib.Path(dataset.__file__).parent
        offenders = []
        for path in list((root / "one").glob("*.py")) + [root / "ai_sdk_adapter.py"]:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                    "dataset"
                ):
                    offenders.append(path.name)
        assert offenders == []


if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(
        __file__,
        "agent_app.dataset",
        preview=False,
    )
