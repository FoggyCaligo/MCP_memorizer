"""Host-controlled extraction, search selectors and local graph persistence."""
import asyncio
import pytest
from mcp_memorizer import Memorizer, ModelFactExtractor
from mcp_memorizer.manager import MemorySearchInput

class StubSegmenter:
    def segment(self, text):
        return [text]
    def close(self):
        pass

class StubModel:
    def __init__(self):
        self.calls = 0
    async def extract(self, messages, schema):
        self.calls += 1
        assert "assistant_final_answer" in messages[1]["content"]
        return {"facts": ["likes apples"]}

def test_round_trip(tmp_path):
    model = StubModel()
    store = Memorizer(tmp_path, user_id="a", segmenter=StubSegmenter(),
                      extractor=ModelFactExtractor(model))
    assert store.search(limit=5)["memories"] == []
    result = asyncio.run(store.after_response(
        user_text="I like apples", final_answer="Okay", turn_id="t1"))
    assert result["saved"] == 1
    assert model.calls == 1
    assert store.search(keyword="likes")["nodes"]
    assert store.search(limit=5)["memories"]
    with pytest.raises(ValueError):
        store.search(node_id=1, keyword="other")
    store.close()

def test_selector_validation():
    with pytest.raises(ValueError):
        MemorySearchInput()
    with pytest.raises(ValueError):
        MemorySearchInput(limit=51)
