"""Prevent memory policy from leaking back into host main prompts."""
from mcp_memorizer.policy import (
    MEMORY_SEARCH_DESCRIPTION, MEMORY_MODEL_CONTEXT,
    MEMORY_MODEL_CONTEXT_KEY,
)
from mcp_memorizer.integrations.mai_tools import register_memory_tools
from mcp_memorizer.memory.working import WorkingGraph

class Registry:
    def __init__(self):
        self.contexts = []
        self.tools = []
    def add_model_context(self, **kwargs):
        self.contexts.append(kwargs)
    def add(self, **kwargs):
        self.tools.append(kwargs)

def test_mai_tool_registration_uses_memorizer_policy():
    registry = Registry()
    register_memory_tools(registry, object(), WorkingGraph(), user_id="local-user")
    assert len(registry.contexts) == 1
    assert registry.contexts[0] == {
        "key": MEMORY_MODEL_CONTEXT_KEY,
        "context": MEMORY_MODEL_CONTEXT,
    }
    assert len(registry.tools) == 1
    assert registry.tools[0]["name"] == "memory_search"
    assert registry.tools[0]["description"] == MEMORY_SEARCH_DESCRIPTION
    assert "after a committed final answer" in MEMORY_SEARCH_DESCRIPTION

def test_mcp_has_only_search_tool():
    from mcp_memorizer.mcp_server import mcp
    import asyncio
    tools = asyncio.run(mcp.list_tools())
    assert [tool.name for tool in tools] == ["memory_search"]
    assert "current conversation" in tools[0].description
