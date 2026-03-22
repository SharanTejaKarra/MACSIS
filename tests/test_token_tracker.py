"""
Tests for the TokenTracker utility.
Covers aggregation, per-agent breakdown, summary formatting, and edge cases.
"""
import pytest
from monitoring.token_tracker import TokenTracker
from memory.state_schema import TokenUsage


def _make_usage(agent: str, inp: int, out: int, model: str = "gpt-4o-mini") -> TokenUsage:
    return TokenUsage(agent_name=agent, input_tokens=inp, output_tokens=out, model=model)


class TestTotal:
    def test_sums_correctly(self):
        log = [
            _make_usage("orchestrator_analyze", 500, 100),
            _make_usage("account_agent", 800, 200),
            _make_usage("feature_agent", 600, 150),
        ]
        tracker = TokenTracker(log)
        totals = tracker.total()

        assert totals["input_tokens"] == 1900
        assert totals["output_tokens"] == 450
        assert totals["total_tokens"] == 2350
        assert totals["num_llm_calls"] == 3

    def test_single_record(self):
        log = [_make_usage("orchestrator_analyze", 100, 50)]
        tracker = TokenTracker(log)
        totals = tracker.total()
        assert totals["total_tokens"] == 150
        assert totals["num_llm_calls"] == 1


class TestByAgent:
    def test_groups_by_agent(self):
        log = [
            _make_usage("account_agent", 500, 100),
            _make_usage("account_agent", 300, 80),
            _make_usage("feature_agent", 400, 90),
        ]
        tracker = TokenTracker(log)
        by_agent = tracker.by_agent()

        assert "account_agent" in by_agent
        assert "feature_agent" in by_agent
        assert by_agent["account_agent"]["input_tokens"] == 800
        assert by_agent["account_agent"]["output_tokens"] == 180
        assert by_agent["account_agent"]["total_tokens"] == 980
        assert by_agent["account_agent"]["calls"] == 2
        assert by_agent["feature_agent"]["calls"] == 1

    def test_single_agent(self):
        log = [_make_usage("orchestrator_analyze", 200, 50)]
        tracker = TokenTracker(log)
        by_agent = tracker.by_agent()
        assert len(by_agent) == 1
        assert by_agent["orchestrator_analyze"]["total_tokens"] == 250


class TestSummaryTable:
    def test_nonempty_output(self):
        log = [
            _make_usage("orchestrator_analyze", 500, 100),
            _make_usage("account_agent", 800, 200),
        ]
        tracker = TokenTracker(log)
        table = tracker.summary_table()

        assert isinstance(table, str)
        assert len(table) > 0

    def test_contains_column_headers(self):
        log = [_make_usage("account_agent", 100, 50)]
        tracker = TokenTracker(log)
        table = tracker.summary_table()

        assert "Agent" in table
        assert "Input" in table
        assert "Output" in table
        assert "Total" in table
        assert "Calls" in table

    def test_contains_agent_names(self):
        log = [
            _make_usage("account_agent", 100, 50),
            _make_usage("feature_agent", 200, 75),
        ]
        tracker = TokenTracker(log)
        table = tracker.summary_table()
        assert "account_agent" in table
        assert "feature_agent" in table
        assert "TOTAL" in table


class TestEmptyLog:
    def test_empty_total(self):
        tracker = TokenTracker([])
        totals = tracker.total()
        assert totals["input_tokens"] == 0
        assert totals["output_tokens"] == 0
        assert totals["total_tokens"] == 0
        assert totals["num_llm_calls"] == 0

    def test_empty_by_agent(self):
        tracker = TokenTracker([])
        assert tracker.by_agent() == {}

    def test_empty_summary_table(self):
        tracker = TokenTracker([])
        table = tracker.summary_table()
        assert "no token usage" in table.lower()


class TestToDict:
    def test_structure(self):
        log = [
            _make_usage("orchestrator_analyze", 500, 100, "gpt-4o-mini"),
            _make_usage("account_agent", 800, 200, "gpt-4o-mini"),
        ]
        tracker = TokenTracker(log)
        d = tracker.to_dict()

        assert "total" in d
        assert "by_agent" in d
        assert "raw_log" in d

        assert d["total"]["total_tokens"] == 1600
        assert len(d["raw_log"]) == 2
        assert d["raw_log"][0]["agent_name"] == "orchestrator_analyze"
        assert d["raw_log"][0]["model"] == "gpt-4o-mini"
        assert "timestamp" in d["raw_log"][0]
