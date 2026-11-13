# Agent integration contracts

The memorizer does not own a model. A host agent supplies its own async
`extract(messages, schema)` adapter. The original MAI extraction prompt is
preserved in `mcp_memorizer/extraction/prompt.py` and is invoked **once after
the final answer is committed**, outside the main tool loop.

## MAI

`mcp_memorizer.integrations.mai.MAIExtractionAdapter` wraps the existing
MAI `LlamaCppAdapter`. `register_memory_search_tool` exposes only
`memory_search` to MAI's tool registry.

MAI still requires changes in `mai/app/runtime.py` to replace its current
in-process memory runtime and background postprocessing, and to call
`Memorizer.after_response` through its final-response lifecycle. Those
changes are NOT included in this repository's alpha.

## Hermes

An **experimental Hermes general plugin** is now included at
`integrations/hermes/`. It registers `memory_search` and uses the confirmed
`post_llm_call` successful-final-response hook with `ctx.llm.complete_structured`
to extract facts using the original MAI prompt. It deliberately excludes
tool evidence when success cannot be independently established. Copy the
directory into `~/.hermes/plugins/mcp-memorizer/`, install the Python package
in Hermes' environment, and enable the plugin. Resolve any collision with
Hermes' existing memory tools explicitly; do not silently override tools.
The plugin is **experimental and not yet tested against a live Hermes host**.
It is intended for one trusted local memory user per running process.

## OpenClaw

An OpenClaw plugin can register the read-only search tool and observe
`agent_end`. The hook must enqueue a post-final-answer job rather than
assuming the process will remain alive to finish an inline model call.
If the host already has an alternative memory plugin, disable conflicting
writes or use separate stores.

## DeepSeek Harness

The official `deepseek-ai/deepseek-harness` uses Cordis plugins and provides
agent/session events. A native plugin should register `memory_search` through
its tools capability and derive committed turn boundaries from the session
event log or documented agent events, **not** a transient assistant-stream end.
The harness is in developer preview, so the event contract must be revalidated.

These are integration design contracts, NOT installed/validated plugins.
MCP-only clients receive search but cannot automatically guarantee post-final
memory writes without the host-side lifecycle integration.

## Security and durability

Do not accept model-selected user IDs. Bind memory to host-authenticated
user/session identity. Persist turn-completion jobs and idempotency keys for
production reliability; the initial SDK uses process-local turn deduplication.
Private chat DBs stay with the host agent.
