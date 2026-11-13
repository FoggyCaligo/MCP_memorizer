"""Experimental Hermes adapter: search-only model tool, post-final extraction.

Install mcp-memorizer into Hermes' Python environment before enabling.
The host must disable any competing memory provider or explicitly authorize
replacement of an existing memory_search tool.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp_memorizer import Memorizer
from mcp_memorizer.extraction.prompt import _FACT_EXTRACTION_SYSTEM
from mcp_memorizer.policy import MEMORY_SEARCH_DESCRIPTION
from mcp_memorizer.extraction.service import _FactExtractionPayload

LOG = logging.getLogger(__name__)

SEARCH_SCHEMA = {
    "description": MEMORY_SEARCH_DESCRIPTION,
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1},
            "node_id": {"type": "integer", "minimum": 1},
        },
        "additionalProperties": False,
    },
}

def _previous_assistant(history, final):
    assistants = [
        item.get("content") for item in (history or [])
        if isinstance(item, dict) and item.get("role") == "assistant"
        and isinstance(item.get("content"), str)
    ]
    if assistants and assistants[-1] == final:
        assistants.pop()
    return assistants[-1] if assistants else None

def register(ctx: Any) -> None:
    # Separate user profiles should use separate plugin processes/databases.
    user_id = os.environ.get("MEMORIZER_USER_ID", "local-user")
    data_dir = Path(os.environ.get("MEMORIZER_DATA_DIR", "Memory_data"))
    store = Memorizer(data_dir=data_dir, user_id=user_id)

    def search(args: dict, **kwargs) -> str:
        del kwargs
        try:
            return json.dumps(store.search(**args), ensure_ascii=False)
        except Exception as exc:
            LOG.warning("memory_search failed: %s", exc)
            return json.dumps({"error": type(exc).__name__, "message": str(exc)})

    def on_final(*, user_message: str, assistant_response: str,
                 conversation_history: list | None = None,
                 turn_id: str | None = None, **kwargs):
        del kwargs
        if not user_message or not assistant_response:
            return
        payload = {
            "latest_user_message": user_message,
            "previous_assistant_message": _previous_assistant(conversation_history, assistant_response),
            "assistant_final_answer": assistant_response,
            # Hermes' post_llm_call does not supply separately authenticated
            # successful non-recall tool evidence. Never promote uncertain
            # tool results or recalled memory to new facts.
            "successful_tool_results": [],
        }
        try:
            result = ctx.llm.complete_structured(
                instructions=_FACT_EXTRACTION_SYSTEM,
                input=[{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                json_schema=_FactExtractionPayload.model_json_schema(),
                purpose="mcp-memorizer.post-response-extract",
                temperature=0.0,
                max_tokens=768,
            )
            extracted = _FactExtractionPayload.model_validate(result.parsed, strict=True)
            asyncio.run(store.save_facts(
                facts=extracted.facts, user_text=user_message, turn_id=turn_id))
        except Exception:
            LOG.exception("post-response memory extraction/storage failed")

    ctx.register_tool(
        name="memory_search", toolset="mcp_memorizer",
        schema=SEARCH_SCHEMA, handler=search,
        description=SEARCH_SCHEMA["description"])
    ctx.register_hook("post_llm_call", on_final)
