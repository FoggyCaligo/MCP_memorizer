"""Isolated contract check for Hermes adapter without a Hermes installation."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def test_hermes_plugin_only_exposes_search_and_saves_after_final(monkeypatch):
    source = Path(__file__).resolve().parents[1] / "integrations" / "hermes" / "__init__.py"
    spec = importlib.util.spec_from_file_location("memorizer_hermes_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    stores = []
    class Store:
        def __init__(self, *args, **kwargs):
            self.saved = []
            stores.append(self)
        def search(self, **kwargs):
            return {"nodes": [], "query": kwargs}
        async def save_facts(self, **kwargs):
            self.saved.append(kwargs)
    monkeypatch.setattr(module, "Memorizer", Store)

    class FakeLLM:
        def __init__(self):
            self.calls = []
        def complete_structured(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(parsed={"facts": ["New project plan"]})

    class FakeContext:
        def __init__(self):
            self.tools = []
            self.hooks = {}
            self.llm = FakeLLM()
        def register_tool(self, **kwargs):
            self.tools.append(kwargs)
        def register_hook(self, name, callback):
            self.hooks[name] = callback

    ctx = FakeContext()
    module.register(ctx)
    assert [item["name"] for item in ctx.tools] == ["memory_search"]
    assert ctx.llm.calls == []
    ctx.hooks["post_llm_call"](
        user_message="I am building a memory agent",
        assistant_response="Understood.",
        conversation_history=[],
        turn_id="turn-1",
    )
    assert len(ctx.llm.calls) == 1
    assert stores[0].saved[0]["facts"] == ["New project plan"]
    assert stores[0].saved[0]["user_text"] == "I am building a memory agent"
