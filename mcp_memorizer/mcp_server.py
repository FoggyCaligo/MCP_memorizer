"""Read-only MCP tool surface: main model may search but never save."""
from __future__ import annotations
import os
from mcp.server.fastmcp import FastMCP
from .manager import Memorizer
from .policy import MEMORY_SEARCH_DESCRIPTION, MEMORY_MODEL_CONTEXT

mcp = FastMCP("MCP_memorizer")
# The same authoritative wording is shared with native MAI/Hermes adapters.
memory_search_policy = MEMORY_SEARCH_DESCRIPTION
_store_instance: Memorizer | None = None

def _store() -> Memorizer:
    global _store_instance
    if _store_instance is None:
        _store_instance = Memorizer(
            data_dir=os.environ.get("MEMORIZER_DATA_DIR", "Memory_data"),
            user_id=os.environ.get("MEMORIZER_USER_ID", "local-user"))
    return _store_instance

@mcp.tool()
def memory_search(node_id: int | None = None, keyword: str | None = None,
                  limit: int | None = None) -> dict:
    """Read-only memory search (three modes). See shared policy for details."""
    return _store().search(node_id=node_id, keyword=keyword, limit=limit)

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
