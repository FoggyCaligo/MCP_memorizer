# Architecture at a glance

MCP_memorizer is a **local SQLite memory library and read-only MCP search server**. It has **no bundled inference model**. Any MCP client can connect for search; a host that wants to save memories must also call the Python SDK.

```text
AI host / MCP client
  ├── memory_search(query | limit | node_id) ──> MCP stdio server ──┐
  └── completed answer + model extraction adapter ──> Python SDK ───┤
                                                                  ▼
                                               MemoryRuntime + RecallService
                                                 ├── SQLite graph: Fact, Concept,
                                                 │   User Anchor, Utterance, Evidence
                                                 ├── Concept search: exact + FTS5
                                                 └── Sentence_Breaker -> Concept terms
```

| Component | Meaning |
|---|---|
| **User Anchor** | The current user's identity boundary, selected by the host |
| **Fact** | Reusable information extracted or supplied by the host |
| **Concept** | Indexed word/segment linked to stored Fact or historical Utterance |
| **Utterance / Evidence** | Past user text node / underlying recorded source (not every Fact has a direct evidence pointer) |
| **WorkingGraph** | Temporary per-request collection of recalled nodes and connections |

The SQLite database stores `nodes`, `edges`, `user_anchors`, `evidence`, and Concept exact/FTS5 indexes. Facts are linked to users using `asserted_fact` and to Concepts using `mentions`. Sentence_Breaker is a **separate dependency** used to segment facts; its own SQLite file must also be backed up.

**Read flow:** parse `query` → run existing lexical Concept search per term → collect user-owned Fact/Utterance nodes → combine using AND/OR/NOT → apply final `limit` → return content-bearing nodes. Recent overview and node expansion are separate search modes; see [recall](recall.md).

**Write flow:** after the host confirms a final answer, it invokes extraction/persistence through the SDK → Fact nodes and Concept links are stored. The MCP tool itself **does not write**; see [extraction](extraction.md).

The host handles authentication, model execution, prompt/tool orchestration, completed-answer timing, persistence retry policy, and private database paths. Retrieval is lexical (not semantic), does not merge paraphrases automatically, and does not resolve conflicting facts by itself. This is an alpha project, not a validated multi-tenant memory service.

Code entry points: `mcp_memorizer/mcp_server.py` (MCP), `manager.py` (SDK), `memory/runtime.py` (lifecycle), `memory/recall/` (search), `memory/index/` (FTS5), `memory/graph/` (SQLite graph).

[Start here: README](../README.md) · [Host integration](integrations.md) · [Sentence_Breaker](sentence-breaker.md)
