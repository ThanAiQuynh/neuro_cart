# add this to head of function upgrade in first alembic migration
```
    # enable citext & vector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS ops")
    op.execute("CREATE SCHEMA IF NOT EXISTS rag")
    op.execute("CREATE SCHEMA IF NOT EXISTS chat")
    op.execute("CREATE SCHEMA IF NOT EXISTS mcp")
```