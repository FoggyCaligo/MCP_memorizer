# Memory search reference

The public, **read-only** stdio MCP tool is `memory_search`. Clients may prefix the name, such as `memorizer__memory_search`. The host sets the current user's identity: **never pass `user_id` as a tool argument**.

## Arguments

| Argument | Usage |
|---|---|
| `query: string` | Keyword or Boolean search across saved facts and past utterances; optional `limit` |
| `limit: positive int` | With `query`: cap returned memories. Alone: recent-memory overview, **required 1–50** |
| `node_id: positive int` | Expand a previously returned node by one hop; cannot combine with `query` or `limit` |

`query` replaces the former `keyword` argument. Calls with neither `query`, `node_id`, nor `limit` are invalid.

## Query syntax

| Operator | Also accepted | Meaning |
|---|---|---|
| `AND` | `&` | Both terms match the **same memory node** |
| `OR` | `|` | Either term matches |
| `NOT` | `!` | Exclude nodes matching the term/expression |
| `( ... )` | — | Group conditions |

Priority is **NOT > AND > OR**. Quote multiword search terms with single or double quotes. For example:

```text
("병력" | "질환" | "질병" | "아픔" | "disease") & ("어릴 적" | "어린 시절" | "유년기" | "childhood")
```

`query="질환 AND NOT 감기"` returns nodes matched by `질환` but not by `감기`. `query="NOT 감기"` searches the **current user's** available Fact/Utterance collection and excludes nodes matched by `감기`. A plain query such as `query="어린 시절 질환"` keeps the previous whitespace-based keyword lookup behavior. The operators filter **existing keyword search results**, not literal string substrings of each stored text.

## Search internals and limits

1. Parse query terms and operators (plain queries use legacy whitespace splitting).
2. For each term, look up Concept nodes using exact match then SQLite FTS5; at most **12 Concept candidates** are considered per term by default.
3. Follow `mentions` links to user-owned Fact/Utterance nodes.
4. Filter memory-node IDs with AND/OR/NOT, rank selected nodes and apply `limit` **after** Boolean evaluation.
5. Return content-bearing nodes with IDs, timestamps, provenance/evidence fields where available. `node_id` can then expand a selected node.

No embedding-based semantic search or automatic synonym/translation expansion is included. An empty result may mean no lexical hit, not that the user never discussed the topic. A `limit`-bounded result is not the entire database. Retrieval rank is not a rule for resolving contradictory facts: the host should compare time scope and explicit user corrections.

## Recent overview / node expansion

`memory_search(limit=10)` returns up to 10 recent user-owned memories linked to the user's anchor, ranked by `last_seen_at` and ID. It is **not** a complete memory dump. `memory_search(node_id=123)` retrieves one-hop graph context for an existing node and its user-anchor path; a different user's anchor is not permitted.

For host setup and writing behavior see [integration guide](integrations.md). For the data model see [architecture](architecture.md).
