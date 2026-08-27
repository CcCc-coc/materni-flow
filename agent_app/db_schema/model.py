# -*- coding: utf-8 -*-

"""
The intermediate representation between reflection and encoding.

``extractor.py`` fills these in from SQLAlchemy metadata, ``encoder.py`` turns
them into the compact string the agent is given. Nothing else reads them.

**Every field here has a reader in the encoder.** The models used to mirror
SQLAlchemy's ``Column`` and ``ForeignKey`` field for field -- ``autoincrement``,
``computed``, ``identity``, ``deferrable``, ``onupdate`` and a dozen others --
none of which anything downstream looked at. Extracting a field nobody encodes
costs reflection time and reads as a promise the output does not keep. Add one
together with the encoder line that emits it, not before.
"""

from pydantic import BaseModel, Field

from ..constants import DbTypeEnum, LLMTypeEnum, TableTypeEnum


class ForeignKeyInfo(BaseModel):
    """A column-level foreign key. ``name`` is the target, as ``table.column``."""

    name: str = Field()


class ColumnInfo(BaseModel):
    """
    Ref: https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Column
    """

    name: str = Field()
    #: The dialect's own spelling, e.g. ``VARCHAR(50)``. Kept as the fallback
    #: label for a type the LLM vocabulary has no entry for.
    type: str = Field()
    llm_type: LLMTypeEnum | None = Field(default=None)
    nullable: bool = Field(default=False)
    index: bool | None = Field(default=None)
    unique: bool | None = Field(default=None)
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)


class TableInfo(BaseModel):
    """
    Ref: https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Table
    """

    name: str = Field()
    table_type: TableTypeEnum = Field(default=TableTypeEnum.TABLE)
    #: Column names, not columns. The encoder marks a column ``*PK`` by looking
    #: its name up here, which is why ``ColumnInfo`` carries no primary-key flag.
    primary_key: list[str] = Field(default_factory=list)
    columns: list[ColumnInfo] = Field(default_factory=list)


class SchemaInfo(BaseModel):
    name: str = Field()
    tables: list[TableInfo] = Field(default_factory=list)


class DatabaseInfo(BaseModel):
    name: str = Field()
    #: Labels the outermost block, so the agent knows which SQL dialect to write.
    db_type: DbTypeEnum = Field()
    schemas: list[SchemaInfo] = Field(default_factory=list)
