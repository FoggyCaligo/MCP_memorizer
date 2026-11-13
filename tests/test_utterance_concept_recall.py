"""Regression coverage for user-owned Fact + Utterance concept recall."""
from datetime import datetime, timezone

from mcp_memorizer.memory.graph.repository import MemoryGraphRepository
from mcp_memorizer.memory.index.base import ConceptHit
from mcp_memorizer.memory.recall.service import RecallService
from mcp_memorizer.memory.working import WorkingGraph


class StaticConceptIndex:
    def __init__(self, concept_id):
        self.concept_id = concept_id

    def search(self, queries, *, limit):
        return (ConceptHit(node_id=self.concept_id, score=1.0, match_kind="exact"),)


def _graph(tmp_path):
    now = datetime.now(timezone.utc)
    graph = MemoryGraphRepository(tmp_path / "memory.sqlite3")
    alice = graph.ensure_user_anchor("alice", now=now)
    bob = graph.ensure_user_anchor("bob", now=now)
    concept, _ = graph.get_or_create_concept("ADHD", now=now)

    fact, _ = graph.get_or_create_fact(
        user_id="alice", text="Alice mentioned ADHD", now=now
    )
    graph.add_typed_edge(alice.id, fact.id, "asserted_fact", provenance="user_assertion", now=now)
    graph.add_typed_edge(fact.id, concept.id, "mentions", provenance="fact_index", now=now)

    evidence = graph.record_evidence("user_utterance", "Alice's original ADHD account", now=now)
    utterance = graph.create_utterance_node(user_id="alice", evidence=evidence, now=now)
    graph.add_typed_edge(alice.id, utterance.id, "spoke", provenance="user_utterance", now=now)
    graph.add_typed_edge(utterance.id, concept.id, "mentions", provenance="utterance_index", now=now)

    other_evidence = graph.record_evidence("user_utterance", "Bob's private ADHD account", now=now)
    other = graph.create_utterance_node(user_id="bob", evidence=other_evidence, now=now)
    graph.add_typed_edge(bob.id, other.id, "spoke", provenance="user_utterance", now=now)
    graph.add_typed_edge(other.id, concept.id, "mentions", provenance="utterance_index", now=now)
    return graph, concept, fact, utterance, other


def test_keyword_recall_returns_fact_and_original_utterance_but_not_other_user(tmp_path):
    graph, concept, fact, utterance, other = _graph(tmp_path)
    try:
        recall = RecallService(graph, StaticConceptIndex(concept.id))
        result = recall.recall_query(user_id="alice", query="ADHD")
        snapshot = result.model_snapshot()
        by_id = {node["node_id"]: node for node in snapshot["nodes"]}

        assert set(by_id) == {fact.id, utterance.id}
        assert by_id[fact.id]["node_type"] == "fact"
        assert by_id[utterance.id]["node_type"] == "utterance"
        assert by_id[utterance.id]["data"] == "Alice's original ADHD account"
        assert by_id[utterance.id]["evidence_id"] is not None
        assert "user_utterance" in by_id[utterance.id]["provenance"]
        assert other.id not in result.nodes
        assert all(node.node_type != "concept" for node in result.nodes.values())
    finally:
        graph.close()


def test_keyword_recall_limit_applies_to_both_fact_and_utterance(tmp_path):
    graph, concept, fact, utterance, _ = _graph(tmp_path)
    try:
        recall = RecallService(graph, StaticConceptIndex(concept.id))
        limited = recall.recall_query(user_id="alice", query="ADHD", limit=1)
        first = [node["node_id"] for node in limited.model_snapshot()["nodes"]]
        repeated = recall.recall_query(user_id="alice", query="ADHD", limit=1)
        assert len(first) == 1
        assert first == [node["node_id"] for node in repeated.model_snapshot()["nodes"]]
        assert first[0] in {fact.id, utterance.id}
    finally:
        graph.close()


def test_node_expansion_still_uses_one_hop(tmp_path):
    graph, concept, fact, utterance, other = _graph(tmp_path)
    try:
        recall = RecallService(graph, StaticConceptIndex(concept.id))
        working = WorkingGraph()
        result = recall.expand_one_hop(working, user_id="alice", node_id=utterance.id)
        assert any(node["node_id"] == utterance.id for node in result["nodes"])
        assert all(node["node_id"] != other.id for node in result["nodes"])
    finally:
        graph.close()
