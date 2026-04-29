"""Backend tests for NEXUS.os Phase 1 iteration 3 - LLM-driven CEO + multi-agent collaboration."""
import os
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ALL_AGENT_IDS = {
    "content_writer", "social_publisher", "seo_specialist", "ad_copywriter", "analytics_agent",
    "frontend_engineer", "backend_engineer", "devops_agent", "qa_agent", "architect_agent",
    "lead_researcher", "outreach_agent", "demo_agent", "negotiator_agent", "crm_agent",
    "user_researcher", "pm_agent", "designer_agent", "roadmap_agent", "feedback_agent",
}


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---- /api/teams (regression) ----
class TestTeams:
    def test_get_teams_returns_4_active_teams_20_agents(self, client):
        r = client.get(f"{API}/teams", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "teams" in data and "locked_teams" in data
        assert data["locked_teams"] == []
        assert [t["id"] for t in data["teams"]] == ["marketing", "engineering", "sales", "product"]
        total = 0
        for t in data["teams"]:
            assert t["status"] == "active"
            assert len(t["agents"]) == 5
            total += 5
        assert total == 20


# ---- /api/orchestrate response shape (new fields) ----
class TestOrchestrateResponseShape:
    def _post(self, client, payload):
        return client.post(f"{API}/orchestrate", json=payload, timeout=60)

    def test_response_has_new_fields(self, client):
        r = self._post(client, {"task": "write a tweet"})
        assert r.status_code == 200
        d = r.json()
        # New required fields per iteration 3
        for key in ("mode", "rationale", "agent_runs", "used_llm",
                    "chosen_agent_id", "chosen_agent_name", "team_id", "team_name",
                    "output", "steps", "request_id", "duration_ms", "task"):
            assert key in d, f"missing field: {key}"
        assert d["mode"] in {"single", "sequential", "parallel"}
        assert isinstance(d["rationale"], str) and len(d["rationale"]) > 0
        assert isinstance(d["agent_runs"], list) and 1 <= len(d["agent_runs"]) <= 3
        assert isinstance(d["used_llm"], bool)

    def test_agent_run_entries_are_well_formed(self, client):
        r = self._post(client, {"task": "write a tweet"})
        d = r.json()
        for run in d["agent_runs"]:
            for k in ("agent_id", "agent_name", "team_id", "team_name", "instruction", "output"):
                assert k in run
            assert run["agent_id"] in ALL_AGENT_IDS
            assert isinstance(run["instruction"], str) and len(run["instruction"]) > 0
            assert isinstance(run["output"], str) and len(run["output"]) > 0

    def test_backwards_compat_fields_match_first_run(self, client):
        r = self._post(client, {"task": "write a tweet"})
        d = r.json()
        first = d["agent_runs"][0]
        assert d["chosen_agent_id"] == first["agent_id"]
        assert d["chosen_agent_name"] == first["agent_name"]
        assert d["team_id"] == first["team_id"]
        assert d["team_name"] == first["team_name"]
        assert d["output"] == first["output"]


# ---- LLM-driven multi-agent flow ----
class TestOrchestrateLLMPlan:
    def test_multi_agent_directive_uses_llm_or_falls_back(self, client):
        """Multi-purpose directive should produce a plan. Prefer LLM; if exhausted, fallback returns single+used_llm=false."""
        task = "Launch a new product: research the audience, write the tweet, and publish it."
        r = client.post(f"{API}/orchestrate", json={"task": task}, timeout=90)
        assert r.status_code == 200
        d = r.json()
        assert d["mode"] in {"single", "sequential", "parallel"}
        assert 1 <= len(d["agent_runs"]) <= 3
        # Either path is valid, but invariants must hold
        if d["used_llm"]:
            # When LLM works, expect multi-agent for this directive
            assert len(d["agent_runs"]) >= 2, "LLM plan should use 2-3 agents for multi-purpose task"
            assert d["mode"] in {"sequential", "parallel"}
        else:
            # Fallback path
            assert d["mode"] == "single"
            assert len(d["agent_runs"]) == 1

    def test_simple_directive_can_be_single(self, client):
        r = client.post(f"{API}/orchestrate", json={"task": "write a tweet"}, timeout=90)
        assert r.status_code == 200
        d = r.json()
        # Single-purpose task may yield single or multi, but all agents must be valid
        for run in d["agent_runs"]:
            assert run["agent_id"] in ALL_AGENT_IDS

    def test_steps_log_includes_ceo_handoff_and_agent_chatter(self, client):
        r = client.post(f"{API}/orchestrate", json={"task": "Launch a product: research, write, publish."}, timeout=90)
        d = r.json()
        steps = d["steps"]
        # First log is "Received directive"
        assert any("Received directive" in s["message"] for s in steps)
        # Plan ready log
        assert any(s["message"].startswith("Plan ready") for s in steps)
        # At least one handoff
        assert any(s["message"].startswith("→ Handing off to") for s in steps)
        # At least one working + success per agent_run
        working = [s for s in steps if s["status"] == "working"]
        success = [s for s in steps if s["status"] == "success"]
        assert len(working) >= len(d["agent_runs"])
        assert len(success) >= len(d["agent_runs"])


# ---- Explicit agent_id bypasses LLM ----
class TestOrchestrateExplicitAgent:
    @pytest.mark.parametrize("agent_id", [
        "frontend_engineer", "pm_agent", "lead_researcher", "negotiator_agent", "devops_agent"
    ])
    def test_explicit_agent_forces_single_no_llm(self, client, agent_id):
        r = client.post(f"{API}/orchestrate", json={"task": "do this thing", "agent_id": agent_id}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d["mode"] == "single"
        assert d["used_llm"] is False
        assert len(d["agent_runs"]) == 1
        assert d["agent_runs"][0]["agent_id"] == agent_id
        assert d["chosen_agent_id"] == agent_id

    def test_invalid_agent_id_returns_404(self, client):
        r = client.post(f"{API}/orchestrate", json={"task": "hi", "agent_id": "ghost_agent"}, timeout=15)
        assert r.status_code == 404

    def test_empty_task_returns_400(self, client):
        r = client.post(f"{API}/orchestrate", json={"task": ""}, timeout=15)
        assert r.status_code == 400

    def test_whitespace_task_returns_400(self, client):
        r = client.post(f"{API}/orchestrate", json={"task": "   "}, timeout=15)
        assert r.status_code == 400
