"""Framework-neutral post-response extraction, using MAI's original policy."""
from __future__ import annotations
import json
from typing import Protocol, Sequence, Any
from pydantic import BaseModel, ConfigDict, ValidationError
from .prompt import _FACT_EXTRACTION_SYSTEM

class _FactExtractionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    facts: list[str]

class FactExtractionError(RuntimeError):
    pass

class FactExtractor(Protocol):
    async def extract(self, *, user_text: str,
        previous_assistant_message: str | None, final_answer: str,
        successful_tool_results: Sequence[str]) -> Sequence[str]: ...

class ModelFactExtractor:
    """Caller supplies an async adapter with extract(messages, schema)."""
    def __init__(self, adapter: Any):
        self.adapter = adapter

    async def extract(self, *, user_text: str,
        previous_assistant_message: str | None = None,
        final_answer: str, successful_tool_results: Sequence[str] = ()) -> tuple[str, ...]:
        payload = {
            "latest_user_message": user_text,
            "previous_assistant_message": previous_assistant_message,
            "assistant_final_answer": final_answer,
            "successful_tool_results": list(successful_tool_results),
        }
        try:
            raw = await self.adapter.extract(
                messages=[
                    {"role": "system", "content": _FACT_EXTRACTION_SYSTEM},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                schema=_FactExtractionPayload.model_json_schema(),
            )
            parsed = (_FactExtractionPayload.model_validate_json(raw, strict=True)
                      if isinstance(raw, str) else
                      _FactExtractionPayload.model_validate(raw, strict=True))
        except (ValidationError, ValueError, TypeError) as exc:
            raise FactExtractionError("invalid structured extraction JSON") from exc
        except Exception as exc:
            raise FactExtractionError(f"model extraction failed: {type(exc).__name__}") from exc
        cleaned: list[str] = []
        for item in parsed.facts:
            fact = item.strip()
            if not fact:
                raise FactExtractionError("empty fact")
            if fact not in cleaned:
                cleaned.append(fact)
        return tuple(cleaned)
