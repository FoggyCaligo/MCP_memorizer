"""Generic async host adapter: store only after a committed final response."""
from __future__ import annotations
from typing import Any, Awaitable, Callable

def with_memory(agent_run: Callable[..., Awaitable[str]], memorizer,
                *, context_builder: Callable[..., dict]):
    """Wrap an async final-answer producer.

    The host MUST use this wrapper as its only run entrypoint to enforce
    post-response capture. Do not call it for partial streaming chunks.
    """
    async def run(*args: Any, **kwargs: Any) -> str:
        answer = await agent_run(*args, **kwargs)
        context = context_builder(*args, **kwargs)
        await memorizer.after_response(final_answer=answer, **context)
        return answer
    return run
