# Ecommerce Electronics DB with Agentic RAG + MCP — Summary
_Last updated: 2025-09-10 06:25:05

This document summarizes the relational data model for an ecommerce web app selling **electronics**, augmented with **Agentic RAG** and **MCP tool logging** on **PostgreSQL + pgvector**.

---

## Table of Contents
1. [Stack & Conventions](#stack--conventions)
2. [Schemas & High‑Level ERD](#schemas--highlevel-erd)
3. [Schema: `core` (Commerce Domain)](#schema-core-commerce-domain)
4. [Schema: `ops` (Operations / Outbox)](#schema-ops-operations--outbox)
5. [Schema: `rag` (Knowledge & Retrieval)](#schema-rag-knowledge--retrieval)
6. [Schema: `chat` (Sessions, Messages, Agent Runs)](#schema-chat-sessions-messages-agent-runs)
7. [Schema: `mcp` (Tool Providers & Calls)](#schema-mcp-tool-providers--calls)
8. [Soft‑Delete Strategy](#softdelete-strategy)
9. [Indexing & Performance](#indexing--performance)
10. [Views & Sample Queries](#views--sample-queries)
11. [Data Lifecycle, Privacy & Retention](#data-lifecycle-privacy--retention)
12. [Migration & Ops Checklist](#migration--ops-checklist)

---

## Stack & Conventions
- **DBMS:** PostgreSQL (14+) with extensions: `uuid-ossp`, `pgcrypto`, `vector` (pgvector).
- **Encoding:** UTF-8; timezone UTC storage with `TIMESTAMPTZ`.
- **IDs:** UUID v4 primary keys; natural keys (slug, sku) via **partial unique indexes** to support soft delete.
- **Documents & attributes:** `JSONB` for flexible specs/attributes; **GIN** indexes where needed.
- **Embeddings:** `VECTOR(N)` (set `N` to your model, e.g., 1024/1536/3072).
- **Naming:** snake_case tables/columns; singular table names per domain choice.
- **Tenancy:** single-tenant (can add `tenant_id` if multi-tenant later).

### Core extensions bootstrap
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";
```

---

## Schemas & High‑Level ERD

**Schemas:**
- `core` — users/customers, catalog, inventory, pricing, carts, orders, payments, shipments, returns, reviews.
- `ops` — event outbox for integrations/ETL.
- `rag` — knowledge sources, documents, versions, chunks (with embeddings), retrieval logs, citations.
- `chat` — chat sessions/messages, agent runs, message↔citation bridge.
- `mcp` — tool providers and tool call logs bound to agent runs.

**Relationship sketch (Mermaid):**
```mermaid erDiagram
  users               ||--o| customers : maps
  brands              ||--o{ products : has
  categories          ||--o{ product_categories : link
  products            ||--o{ product_variants : has
  product_variants    ||--o{ inventory_levels : tracked_at_location
  carts               ||--o{ cart_items : contains
  orders              ||--o{ order_items : contains
  orders              ||--o{ payments : paid_by
  orders              ||--o{ shipments : fulfilled_by
  shipments           ||--o{ shipment_items : for_items
  returns             ||--o{ return_items : for_items
  customers           ||--o{ reviews : writes

  knowledge_sources   ||--o{ documents : provides
  documents           ||--o{ document_versions : versions
  document_versions   ||--o{ document_chunks : chunks
  retrieval_logs      ||--o{ citations : produces
  chat_sessions       ||--o{ chat_messages : has
  chat_messages       ||--o{ message_citations : cites
  chat_sessions       ||--o{ agent_runs : spawns
  agent_runs          ||--o{ tool_calls : executes
```
> Diagram is indicative; see table lists below for exact foreign keys.

---

## Schema: `core` (Commerce Domain)

### Identity & RBAC
- **users** — login + profile (`email[CITEXT]`, `password_hash`, `is_active`, timestamps).  
  _Soft delete:_ via `deleted_at` (optional).  
- **roles**, **user_roles** — RBAC mapping (e.g., `admin`, `staff`, `customer`).

### Customer & Addresses
- **customers** — 1:1 (optional) to `users`, loyalty `tier`.  
- **addresses** — shipping/billing book (`label`, `recipient`, `phone`, `line1..`, `country_code`).

### Catalog
- **brands** — brand dictionary (`name`, `slug`).  
- **categories** — tree via `parent_id`, `name`, `slug`.  
- **products** — core entity (`brand_id`, `name`, `slug`, `model_number`, `specs JSONB`, `description`, `is_published`).  
- **product_categories** — M:N between `products` and `categories`.  
- **product_variants** — concrete sellable variant (`sku`, `attributes JSONB`, `barcode`, `weight_grams`, `dimensions_mm JSONB`, `status`).  
- **media_assets** — images/files linked by `owner_type` (`product|variant`) + `owner_id`.

### Inventory & Pricing
- **inventory_locations** — warehouses (`code`, `name`, `address`).  
- **inventory_levels** — per-variant per-location stock (`on_hand`, `reserved`).  
- **prices** — list prices over time (`currency`, `amount`, `compare_at`, `effective_at`).

### Carts & Orders
- **carts** / **cart_items** — active/bounced carts; item price snapshot kept at add-time.  
- **orders** — header (`code`, `customer_id`, address refs, amounts by component, `status`).  
- **order_items** — line snapshot (`product_id`, `variant_id`, `name`, `sku`, `attributes`, `qty`, `unit_price`, `line_total`).  
- **payments** — provider (`vnpay/momo/stripe`), `status`, `amount`, `txn_ref`, `raw_payload`.  
- **shipments** / **shipment_items** — carrier, tracking, `status`, timestamps.  
- **returns** / **return_items** — RMA workflow (`status`, `reason`).

### UGC
- **reviews** — ratings 1–5, `title`, `body`, moderatable `status` (`pending/published/hidden`).

---

## Schema: `ops` (Operations / Outbox)
- **event_outbox** — durable integration log: `aggregate`, `aggregate_id`, `event_type`, `payload JSONB`, `published BOOLEAN`, `created_at`.
  - Use for CDC-style fanout to Search/BI/CRM; purge or archive after confirmation.

---

## Schema: `rag` (Knowledge & Retrieval)
- **knowledge_sources** — provenance (`kind: manual/datasheet/warranty/faq/blog/web`, `url`, `metadata`).  
- **documents** — links to catalog (`product_id`, `variant_id`), `title`, `lang`, `tags[]`, `latest_version_id`.  
- **document_versions** — `version`, `raw_text`, `metadata` (e.g., parser, checksum).  
- **document_chunks** — chunked text with `embedding VECTOR(N)`, `tokens`, `metadata`. **Primary vector-search table.**  
- **retrieval_logs** — per-query log: `query_text`, `query_embedding`, `top_k`, `latency_ms`.  
- **citations** — `retrieval_id` + `chunk_id` + `rank`, `score`.

**Key idea:** tie product/variant docs so the assistant can answer *spec-, warranty-, setup-* questions with traceable citations.

---

## Schema: `chat` (Sessions, Messages, Agent Runs)
- **chat_sessions** — conversation container (`user_id?`, `channel`, `persona`, `created_at`, `last_active_at`).  
- **chat_messages** — `role (user/assistant/tool/system)`, `content`, token counts.  
- **message_citations** — M:N to `rag.document_chunks` with small `snippet` for UI hovers.  
- **agent_runs** — a single planning/execution cycle (`objective`, `status`, `started_at/finished_at`).

---

## Schema: `mcp` (Tool Providers & Calls)
- **tool_providers** — MCP endpoints (`name`, `endpoint`, `metadata`).  
- **tool_calls** — bound to `agent_runs`: `tool_name`, `arguments JSONB`, `result JSONB`, `status`, `latency_ms`.

---

## Soft‑Delete Strategy
- Prefer **`deleted_at TIMESTAMPTZ NULL`** (+ optional `deleted_by`, `delete_reason`).  
- **Partial unique indexes** so `slug`/`sku` can be reused after deletion:
```sql
CREATE UNIQUE INDEX ux_products_slug_live
ON core.products (slug) WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX ux_variants_sku_live
ON core.product_variants (sku) WHERE deleted_at IS NULL;
```
- Vector table partial index to exclude deleted chunks:
```sql
CREATE INDEX rag_document_chunks_embedding_live
ON rag.document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100) WHERE deleted_at IS NULL;
```
- **Do not soft-delete** accounting-critical tables (`orders`, `payments`, `shipments`, `returns`). Instead, disable/obfuscate PII if required by policy.

---

## Indexing & Performance
- **Temporal/reporting:** `orders(created_at, status)`, `payments(order_id)`, `order_items(variant_id)`.
- **Searchable JSONB:** GIN on `products(specs)`; GIN on `product_variants(attributes)` when facet filtering.
- **Vector search:** IVFFLAT/HNSW on `rag.document_chunks(embedding)`; ensure `ANALYZE` & proper `lists/ef_search` tuning.
- **Chat logs:** `chat_messages(session_id, created_at)` for fast pagination; `agent_runs(session_id, started_at)`.

---

## Views & Sample Queries

### Convenience “live” views
```sql
CREATE OR REPLACE VIEW core_live_products AS
SELECT * FROM core.products WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW core_live_variants AS
SELECT * FROM core.product_variants WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW rag_live_chunks AS
SELECT * FROM rag.document_chunks WHERE deleted_at IS NULL;
```

### Product listing with faceted filters (example)
```sql
SELECT p.id, p.name, v.id AS variant_id, v.sku, pr.amount AS price
FROM core_live_products p
JOIN core.product_variants v ON v.product_id = p.id AND v.deleted_at IS NULL
LEFT JOIN LATERAL (
  SELECT amount FROM core.prices pr
  WHERE pr.variant_id = v.id AND pr.deleted_at IS NULL
  ORDER BY pr.effective_at DESC
  LIMIT 1
) pr ON TRUE
WHERE (p.specs @> '{{"brand":"ACME"}}'::jsonb OR :brand IS NULL)
  AND (v.attributes @> '{{"storage":"256GB"}}'::jsonb OR :storage IS NULL);
```

### RAG retrieval scoped by product (cosine distance)
```sql
-- :query_vec is a parameter of type vector
SELECT c.id, c.content, (1 - (c.embedding <=> :query_vec)) AS similarity
FROM rag_live_chunks c
JOIN rag.documents d ON d.id = c.document_id AND d.deleted_at IS NULL
WHERE (d.product_id = :product_id OR :product_id IS NULL)
ORDER BY c.embedding <=> :query_vec
LIMIT 5;
```

### Agent observability: last tool calls for a session
```sql
SELECT r.id AS run_id, r.objective, tc.tool_name, tc.status, tc.latency_ms, tc.created_at
FROM chat.agent_runs r
JOIN mcp.tool_calls tc ON tc.run_id = r.id
WHERE r.session_id = :session_id
ORDER BY tc.created_at DESC
LIMIT 50;
```

---

## Data Lifecycle, Privacy & Retention
- **Carts:** auto-expire & hard-delete abandoned carts (> 60–90 days).  
- **Chat sessions:** retain N days unless user opts to keep; strip PII where feasible.  
- **Outbox:** archive after published confirmation.  
- **RMA/Accounting:** immutable per legal retention (country-specific).  
- **PII Minimization:** store only required fields; encrypt secrets; consider field-level encryption for `phone` if policy demands.

---

## Migration & Ops Checklist
- [ ] Enable extensions (`uuid-ossp`, `pgcrypto`, `vector`).  
- [ ] Create schemas: `core`, `ops`, `rag`, `chat`, `mcp`.  
- [ ] Create baseline tables per schema.  
- [ ] Add **soft-delete columns** (`deleted_at`, `deleted_by`, `delete_reason`) on selected tables.  
- [ ] Replace natural-key constraints with **partial unique indexes**.  
- [ ] Create **vector index** on `rag.document_chunks(embedding)` (partial WHERE `deleted_at IS NULL`).  
- [ ] Add GIN indexes for `specs` / `attributes` if using faceted filters.  
- [ ] Seed dictionaries: `roles`, `brands`, `categories`, `inventory_locations`.  
- [ ] Implement outbox dispatcher & retry/backoff.  
- [ ] Implement ingestion pipeline: document → version → chunk + embed.  
- [ ] Implement `message_citations` in chat UI to show sources.  
- [ ] Backup/restore plan and VACUUM/ANALYZE schedule.  
- [ ] Add RLS or service-role split if multi-tenant or strict data boundaries are needed.

---

### Notes
- Adjust `VECTOR(N)` to your embedding model size.  
- Prefer **bigint monetary** in minor units if you need exact integer math; otherwise `NUMERIC(12,2)` is acceptable for VND/fiat.  
- If you expect high write throughput on vector table, consider dedicated tablespace & autovacuum tuning.
