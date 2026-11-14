"""Adapter for MAI's existing LlamaCppAdapter and ToolRegistry.

Import this only from MAI, never inside the portable memorizer engine.
"""
from __future__ import annotations
from mcp_memorizer.manager import Memorizer, MemorySearchInput
from mcp_memorizer.policy import MEMORY_MODEL_CONTEXT_KEY, MEMORY_MODEL_CONTEXT, MEMORY_SEARCH_DESCRIPTION

class MAIExtractionAdapter:
    def __init__(self, llm_adapter):
        self.llm_adapter = llm_adapter

    async def extract(self, messages, schema):
        from mai.llm.models import ChatRequest
        request = ChatRequest(
            messages=tuple(messages), tools=(), think=False, response_format=schema)
        turn = await self.llm_adapter.chat(request)
        return turn.content

def register_memory_search_tool(registry, memory: Memorizer) -> None:
    """Only memory_search is exposed to MAI's model tool registry."""
    async def search(node_id=None, query=None, limit=None):
        return memory.search(node_id=node_id, query=query, limit=limit)
    registry.add_model_context(key=MEMORY_MODEL_CONTEXT_KEY, context=MEMORY_MODEL_CONTEXT)
    registry.add(
        name="memory_search",
        description=MEMORY_SEARCH_DESCRIPTION,
        input_model=MemorySearchInput,
        handler=search,
        category="memory",
    )
