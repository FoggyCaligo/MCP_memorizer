# 에이전트별 MCP_memorizer 연동 계약

MCP_memorizer는 자체 추론 모델을 소유하지 않는다. 호스트 에이전트가 비동기
`extract(messages, schema)` adapter. The original MAI extraction prompt is
preserved in `mcp_memorizer/extraction/prompt.py` and is invoked **once after
the final answer is committed**, outside the main tool loop.

## MAI

메모리 엔진의 구현과 검색 계약은 [엔진 구조](architecture.md) 및 [회수](recall.md)를 따른다.

`mcp_memorizer.integrations.mai.MAIExtractionAdapter` wraps the existing
MAI `LlamaCppAdapter`. `register_memory_search_tool` exposes only
`memory_search` to MAI's tool registry.

MAI의 현재 `dev`는 외부 `MCP_memorizer` 패키지를 사용하고 메모리 검색을
`memorizer__memory_search` MCP 도구로 연결한다. 저장은 MAI 호스트가 최종 답변 확정 후
독립 패키지 추출·저장 서비스를 호출하는 작업으로 관리한다. 호스트의 호출 시점과 오류/비동기
처리 정책은 MAI 저장소의 `mai/app/runtime.py` 및 `docs/memory.md`가 소유한다.
`Memorizer.after_response` SDK 예시가 MAI의 모든 내부 호출 경로와 동일하다는 뜻은 아니다.

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
