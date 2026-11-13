"""Read-only MCP tool surface: main model may search but never save."""
from __future__ import annotations
import os
from mcp.server.fastmcp import FastMCP
from .manager import Memorizer

mcp = FastMCP("MCP_memorizer")
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
    """Search persistent memory using the original MAI three modes.

    keyword: topic/free-text recall, optionally limit the number of facts.
    node_id: expand an owned graph node by one hop. Forbid keyword/limit.
    limit only: bounded recent-memory overview (required 1..50).
    An empty or bounded search result does NOT prove other memories are absent.
    Current user statements and current tool results override older memories.
    Among conflicting Fact nodes of the same subject/property/time scope, use
    the latest created_at, not recall rank or occurrence count.
    """
    return _store().search(node_id=node_id, keyword=keyword, limit=limit)

def main() -> None:
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
