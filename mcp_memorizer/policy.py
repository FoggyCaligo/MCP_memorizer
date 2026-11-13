"""Authoritative model-facing memory policy, shared by all integrations.

Keep host-specific agent instructions out of the host's main system prompt.
Main models receive read-only memory_search; the host owns post-final storage.
"""
MEMORY_MODEL_CONTEXT_KEY = "persistent_memory_temporal_precedence"
MEMORY_MODEL_CONTEXT = {
    "kind": "temporal_precedence",
    "instruction": (
        "Information recalled from persistent memory describes past conversations or past known state. "
        "Use recalled memory only as supporting context. The user's current message and current tool results "
        "take precedence whenever they differ from, update, or supersede recalled memory. "
        "When retrieved Fact nodes make incompatible claims about the same subject, property, and time scope, "
        "treat the Fact node with the latest created_at as authoritative for that conflict. "
        "Do not use retrieval rank, tool-call order, occurrence_count, or last_seen_at in place of created_at. "
        "Preserve facts about different historical periods; later recording alone does not erase historical facts. "
        "If conflicting nodes have indistinguishable created_at timestamps or incompatible provenance that "
        "prevents a reliable chronological resolution, state the conflict instead of inventing certainty."
    ),
}

MEMORY_SEARCH_DESCRIPTION = (
    "Retrieve persistent memory in one of three modes: keyword for topic-based recall "
    "(e.g. hobbies, preferences, events), node_id to expand a known graph node, "
    "or neither keyword nor node_id for a recent-memory overview. The overview mode "
    "REQUIRES an explicit limit from 1 to 50; keyword recall supports an optional "
    "positive limit and node_id forbids limit. A recent overview is not the complete "
    "memory database. A bounded or empty result does not prove other memories are absent. "
    "Use memory_search when user-specific information is needed but not present in "
    "the current conversation; consult the registered tool schema before calling it. "
    "This tool is host-local only; do not attempt remote execution or supply a remote-computer selector. "
    "The model can SEARCH but cannot SAVE memory: after a committed final answer, "
    "the host independently calls its extraction model and persists the resulting facts."
)
