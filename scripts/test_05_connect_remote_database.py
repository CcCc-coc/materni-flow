# -*- coding: utf-8 -*-

import sqlalchemy as sa
from agent_app.api import one

engine = one.remote_postgres_engine
stmt = sa.text("SELECT 1;")
with engine.connect() as conn:
    result = conn.execute(stmt)
    print(result.fetchall())
