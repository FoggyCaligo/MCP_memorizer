# MCP_memorizer

**SQLite-based long-term memory search for AI agents.** An MCP client can connect to the read-only `memory_search` tool; an application that wants to **save** memories must also integrate the Python SDK. No MAI installation is required.

- **Search:** exact/FTS5 Concept lookup, Boolean `AND`/`OR`/`NOT`, and graph-node expansion.
- **Store:** host-controlled fact extraction and persistence after an answer is finalized (Python SDK, **not** an MCP write tool).
- **Data:** local SQLite files, isolated by the configured `user_id`. The package does not include an LLM.

> **Important:** Connecting the MCP server alone does **not** automatically remember conversations. A fresh database has no conversation facts to retrieve until a host saves them.

## Quick start (MCP search)

Requirements: Python **3.11+**, SQLite with FTS5, Git (for the Sentence_Breaker dependency).

```bash
git clone https://github.com/FoggyCaligo/MCP_memorizer.git
cd MCP_memorizer
git switch dev
python -m pip install -e ".[mcp]"
```

Configure any MCP client that supports local **stdio** servers. Example configuration (the surrounding JSON key may differ by client):

```json
{
  "mcpServers": {
    "memorizer": {
      "command": "/absolute/path/to/python",
      "args": ["-m", "mcp_memorizer.mcp_server"],
      "env": {
        "MEMORIZER_USER_ID": "local-user",
        "MEMORIZER_DATA_DIR": "/absolute/path/to/private/Memory_data"
      }
    }
  }
}
```

Use the Python interpreter where the package was installed (on Windows, use the interpreter's Windows path). Replace the example paths with **real absolute paths**. Start/restart the MCP client to connect; the server communicates over stdio, so launching it in a terminal will not open a web interface. Make sure the process has write access to the data directory.

The client will discover **one tool: `memory_search`**. The client may prefix it with its server name (for example `memorizer__memory_search`).

## Search examples

| Tool arguments | Result |
|---|---|
| `{"query":"project plans","limit":10}` | Search user-owned facts by keywords |
| `{"query":"(travel | trip) & NOT cancelled","limit":10}` | Combine and exclude keyword matches |
| `{"limit":10}` | Up to 10 recent memories |
| `{"node_id":123}` | Expand a returned memory node |

For `query`, use **AND** (`&`), **OR** (`|`), **NOT** (`!`) and parentheses; quote multiword terms. Example:

```text
("병력" | "질환" | "질병" | "아픔" | "disease") & ("어릴 적" | "어린 시절" | "유년기" | "childhood")
```

Each term uses the existing lexical search; synonyms/translations are **not** expanded automatically. A single unstructured query retains the previous keyword lookup behavior. `limit` restricts final matches; `node_id` cannot be combined with other selectors. Empty results do not prove an absence of saved memories. See [search details](docs/recall.md).

## How memories get saved (Python SDK)

The MCP server is **read-only**. The host application decides when the assistant's answer is final and calls the SDK; it must supply a model adapter for fact extraction.

For a minimal **manual** example, to seed a memory without an extraction model:

```python
import asyncio
from mcp_memorizer import Memorizer

async def main():
    store = Memorizer(data_dir="./Memory_data", user_id="local-user")
    try:
        await store.save_facts(
            facts=["The user prefers concise explanations."],
            user_text="Please keep explanations concise.",
        )
        print(store.search(query="concise", limit=10))
    finally:
        store.close()

asyncio.run(main())
```

This uses the **same** user ID and data directory as the MCP server. To implement automatic persistence, integrate `ModelFactExtractor` and `after_response(...)` in your host's completed-answer lifecycle; see [host integration](docs/integrations.md) and [extraction rules](docs/extraction.md). Do not expose an unrestricted save operation to the model.

## Storage, privacy and limitations

- Two SQLite files are created in the configured data directory: `memory.sqlite3` and `sentence_breaker.sqlite3`. Back up both. Without `MEMORIZER_DATA_DIR`, the standalone server defaults to a relative `Memory_data` directory.
- Set `MEMORIZER_USER_ID` to an authenticated, stable identity chosen **by the host**, never by the model. For different users, use separate IDs and preferably separate private data directories.
- Memory search uses **lexical** matching, not embeddings or semantic similarity. Retrieval does not automatically resolve contradictory historical facts.
- Persistent post-answer job retries and exactly-once recording across crashes are **not guaranteed**. This is an alpha release (`0.1.0a0`); validate security and behavior before production or multi-tenant deployment.

## Documentation

- [MCP/client + save lifecycle integration](docs/integrations.md)
- [Search syntax and ranking](docs/recall.md)
- [Data model](docs/architecture.md)
- [Fact extraction and storage rules](docs/extraction.md)
- [Sentence_Breaker dependency](docs/sentence-breaker.md)

Originally developed for [MAI](https://github.com/FoggyCaligo/MAI_MyAI_sllm), but usable without it. License: **AGPL-3.0-only**. The [Sentence_Breaker](https://github.com/FoggyCaligo/Sentence_Breaker) dependency has its own license.
