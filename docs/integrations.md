# Integrating MCP_memorizer

MCP_memorizer has **two separate interfaces**. You can use either or both:

| Interface | Purpose | How to connect |
|---|---|---|
| MCP stdio server | Read-only memory lookup | Run `python -m mcp_memorizer.mcp_server` with your MCP client's configuration |
| Python SDK | Write extracted facts, or call search directly | Import `Memorizer` in a Python host process |

**An MCP client can search existing memories immediately after connecting, but it will not automatically save new conversations.** The host must implement persistence separately.

## 1. Connect the MCP server

Install the package using [Quick start](../README.md#quick-start-mcp-search) and configure a local stdio server. Supply:

- `MEMORIZER_USER_ID`: stable authenticated identity (host-controlled, not model-supplied).
- `MEMORIZER_DATA_DIR`: persistent private directory for `memory.sqlite3` and `sentence_breaker.sqlite3`.

Clients may rename/prefix the public `memory_search` tool. The tool accepts exactly `query`, `limit`, and `node_id`; see [recall](recall.md). An empty new database will return no topic matches.

## 2. Save facts after a completed response

To enable long-term memory **writing**, the host chooses a final-answer event and calls the SDK. A typical flow:

1. Authenticate the user and select their stable memory ID and private database.
2. After the **final** answer, pass the current user message, previous assistant message (if relevant), final answer, and successful **non-memory** tool results to a `ModelFactExtractor` adapter.
3. Validate extracted facts, then persist them using `Memorizer.after_response(...)` (or `save_facts(...)` for explicitly supplied facts).
4. Handle extraction failures and shutdown/retry behavior in the host. Do **not** treat lookup results as new independent evidence.

A model adapter must provide `async extract(messages, schema)` and call a host-supplied model that supports structured output. The SDK contains no bundled LLM. See [extraction contract](extraction.md) and the [README manual SDK example](../README.md#how-memories-get-saved-python-sdk).

## What is and is not provided

**Provided:** read-only MCP search, local SQLite persistence via SDK, Fact/Concept graph, user-scoped retrieval, query Boolean operators.

**Not provided by the MCP connection:** automatic transcript ingestion, a `memory_save` tool, login/identity management, hosted HTTP MCP endpoint, shared cloud sync, reliable exactly-once background persistence, or embeddings-based semantic search.

The installed host is responsible for user isolation and access to the data directory. Do not place private SQLite files in public Git repositories.

## Existing integrations

- **MAI:** integrates the search-only MCP server as `memorizer__memory_search`; MAI separately owns post-answer extraction/saving and user identity. [MAI integration details](https://github.com/FoggyCaligo/MAI_MyAI_sllm/blob/dev/docs/memory.md).
- **Hermes:** the included `integrations/hermes` plugin is experimental and has not been end-to-end validated for general host versions.
- **OpenClaw / DeepSeek Harness:** host lifecycle write integration is not shipped as a tested ready-to-install adapter; requires separate host development.

For the underlying structures see [architecture](architecture.md). For keyword semantics see [recall](recall.md).
