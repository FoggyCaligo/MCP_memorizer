"""Host-owned memory search and post-response persistence."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .memory.graph.repository import MemoryGraphRepository
from .memory.index import SqliteFtsConceptIndex
from .memory.recall.service import RecallService
from .memory.runtime import MemoryRuntime
from .memory.segmenter import SentenceBreakerSegmenter
from .memory.working import WorkingGraph
from .extraction.service import ModelFactExtractor

class MemorySearchInput(BaseModel):
    """MAI's original exclusive three-mode query contract."""
    model_config = ConfigDict(extra="forbid")
    node_id: int | None = Field(None, gt=0)
    keyword: str | None = Field(None, min_length=1)
    limit: int | None = Field(None, ge=1)
    @model_validator(mode="after")
    def check(self):
        if self.node_id is not None and (self.keyword is not None or self.limit is not None):
            raise ValueError("node_id forbids keyword and limit")
        if self.node_id is None and self.keyword is None and (self.limit is None or self.limit > 50):
            raise ValueError("overview requires limit 1 to 50")
        return self

class Memorizer:
    def __init__(self, data_dir: str | Path = "Memory_data", *, user_id: str = "local-user",
                 extractor: ModelFactExtractor | None = None, segmenter=None):
        if not user_id.strip():
            raise ValueError("user_id cannot be blank")
        self.user_id = user_id
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.graph = MemoryGraphRepository(self.data_dir / "memory.sqlite3")
        self.index = SqliteFtsConceptIndex(self.data_dir / "memory.sqlite3")
        self.segmenter = segmenter if segmenter is not None else SentenceBreakerSegmenter(
            db_path=str(self.data_dir / "sentence_breaker.sqlite3"))
        self.runtime = MemoryRuntime(
            self.graph, self.index, self.segmenter, RecallService(self.graph, self.index),
            now=lambda: datetime.now(timezone.utc), fact_extractor=extractor)
        self.runtime.ensure_user(self.user_id)
        self._working = WorkingGraph()
        self._write_lock = asyncio.Lock()
        self._saved_turns: set[str] = set()

    def search(self, *, node_id: int | None = None, keyword: str | None = None,
               limit: int | None = None) -> dict[str, object]:
        args = MemorySearchInput(node_id=node_id, keyword=keyword, limit=limit)
        if args.node_id is not None:
            anchor = self.graph.get_user_anchor(self.user_id)
            if anchor is None or (
                args.node_id != anchor.id and
                self.graph.shortest_path_to_user_anchor(args.node_id, self.user_id) is None
            ):
                raise PermissionError("node is not owned by current user")
            return self.runtime.memory_search(self._working, user_id=self.user_id, node_id=args.node_id)
        if args.keyword is None:
            return self.runtime.memory_overview(user_id=self.user_id, limit=args.limit)
        recalled = self.runtime.explicit_recall(user_id=self.user_id, query=args.keyword, limit=args.limit)
        self._working.merge_working(recalled)
        return recalled.model_snapshot()

    async def save_facts(self, *, facts: Sequence[str], user_text: str,
                         turn_id: str | None = None) -> dict[str, object]:
        """Host-only API. NEVER expose this to the model as an MCP tool."""
        if isinstance(facts, (str, bytes)) or any(not isinstance(x, str) or not x.strip() for x in facts):
            raise ValueError("facts must be nonempty strings")
        if not user_text.strip():
            raise ValueError("user_text cannot be blank")
        async with self._write_lock:
            if turn_id and turn_id in self._saved_turns:
                return {"saved": 0, "already_processed": True}
            evidence = self.runtime.record_raw_user_evidence(self.user_id, user_text)
            await self.runtime.finish_turn(
                user_id=self.user_id, user_text=user_text, final_answer="",
                user_evidence=evidence, fact_texts=tuple(dict.fromkeys(facts)))
            if turn_id:
                self._saved_turns.add(turn_id)
            return {"saved": len(set(facts)), "already_processed": False}

    async def after_response(self, *, user_text: str, final_answer: str,
                             previous_assistant_message: str | None = None,
                             successful_tool_results: Sequence[str] = (),
                             turn_id: str | None = None) -> dict[str, object]:
        """Run ONE additional structured extraction after committed final answer."""
        if self.runtime.fact_extractor is None:
            raise RuntimeError("an extraction model adapter is required")
        facts = await self.runtime.extract_facts(
            user_text=user_text, previous_assistant_message=previous_assistant_message,
            final_answer=final_answer, successful_tool_results=successful_tool_results)
        return await self.save_facts(facts=facts, user_text=user_text, turn_id=turn_id)

    def close(self) -> None:
        self.index.close()
        self.graph.close()
        if hasattr(self.segmenter, "close"):
            self.segmenter.close()
