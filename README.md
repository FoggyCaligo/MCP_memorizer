# MCP_memorizer — developer alpha

Independent MAI-derived SQLite memory graph, with a **search-only MCP tool**
and a **host-controlled post-response extraction SDK**.

The main agent can only invoke `memory_search`. It must **not** be given
`memory_save`; extraction and storage are performed by the host after the
final answer is committed. The model chosen by the host is called once more,
with MAI's original structured JSON extraction prompt (`{"facts": [...]}`).

## Installation

```bash
git clone https://github.com/FoggyCaligo/MCP_memorizer.git
cd MCP_memorizer
git switch dev
pip install -e '.[mcp]'
python -m mcp_memorizer.mcp_server
```

Python 3.11+ and SQLite with FTS5 are required. `Sentence_Breaker` is an
MCP_memorizer dependency, not a host-agent dependency.

## Persistent data

Default: `Memory_data/memory.sqlite3` and
`Memory_data/sentence_breaker.sqlite3`. `Memory_data/` is Git-ignored.
Never commit private user data or copy existing MAI databases into a
public repository. To migrate existing data, stop all writers, take consistent
SQLite backups, and explicitly configure the private target path.

## Search — original MAI behavior

```python
from mcp_memorizer import Memorizer
memory = Memorizer(data_dir="./Memory_data", user_id="local-user")
memory.search(keyword="project plans", limit=10)
memory.search(limit=10)
memory.search(node_id=123)
```

MCP stdio registration: command `python`, args
`["-m", "mcp_memorizer.mcp_server"]`, with
`MEMORIZER_USER_ID` and `MEMORIZER_DATA_DIR` set in the server environment.
Do not expose untrusted user_id selection to the language model.

## Post-response automatic persistence (SDK)

```python
from mcp_memorizer import Memorizer, ModelFactExtractor

class Adapter:
    async def extract(self, messages, schema):
        # Host calls its own model with structured JSON output and returns
        # a dict {"facts": ["..."]} or equivalent JSON string.
        ...

memory = Memorizer(extractor=ModelFactExtractor(Adapter()))

# Host calls this AFTER committing the final answer, not during tool rounds.
await memory.after_response(
    user_text=user_text,
    previous_assistant_message=previous_assistant_message,
    final_answer=final_answer,
    successful_tool_results=successful_non_recall_results,
)
```

Other agents can use `mcp_memorizer.lifecycle.with_memory` as a
generic asynchronous wrapper; framework plugins are needed for Hermes,
OpenClaw and DeepSeek Harness to guarantee an end-of-turn callback.
No verified framework-specific plugins are shipped in this alpha.

## Provenance and status

Source preserved from MAI: graph schema, node/edge repository, lexical FTS5
search, recall, working graph, memory runtime, Sentence_Breaker adapter,
and the exact fact extraction prompt. New code supplies the framework-neutral
model adapter, SDK manager and MCP search-only server.

**Important:** MAI itself has NOT been switched to this package.
In-memory `turn_id` deduplication is NOT durable. This is a developer
alpha requiring runtime and multi-user security testing before production.
Do not claim exact-once persistence on crashes.

Original source: https://github.com/FoggyCaligo/MAI_MyAI_sllm/tree/dev/mai/memory
License: AGPL-3.0-only; review Sentence_Breaker's own dependency license.
