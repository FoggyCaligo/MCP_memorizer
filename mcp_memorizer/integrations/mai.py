"""Adapter for MAI's existing LlamaCppAdapter and ToolRegistry.

Import this only from MAI, never inside the portable memorizer engine.
"""
from __future__ import annotations
from mcp_memorizer.manager import Memorizer, MemorySearchInput

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
    async def search(node_id=None, keyword=None, limit=None):
        return memory.search(node_id=node_id, keyword=keyword, limit=limit)
    registry.add(
        name="memory_search",
        description=(
            "Read persistent memory: keyword with optional limit for topic recall; "
            "limit alone (1-50) for recent overview; node_id alone for graph expansion. "
            "Never treat empty or limited search results as proof that other memory is absent. "
            "The model cannot save memory; saving happens automatically after final response."
        ),
        input_model=MemorySearchInput,
        handler=search,
        category="memory",
    )
