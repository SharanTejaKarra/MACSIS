from memory.state_schema import TokenUsage


class TokenTracker:
    """Aggregates token_usage_log into per-agent breakdowns and totals."""

    def __init__(self, usage_log: list[TokenUsage]):
        self._records = usage_log

    def total(self) -> dict:
        """Grand total."""
        input_t = sum(r.input_tokens for r in self._records)
        output_t = sum(r.output_tokens for r in self._records)
        return {
            "input_tokens": input_t,
            "output_tokens": output_t,
            "total_tokens": input_t + output_t,
            "num_llm_calls": len(self._records),
        }

    def by_agent(self) -> dict:
        """Per-agent breakdown."""
        agents = {}
        for r in self._records:
            if r.agent_name not in agents:
                agents[r.agent_name] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
            agents[r.agent_name]["input_tokens"] += r.input_tokens
            agents[r.agent_name]["output_tokens"] += r.output_tokens
            agents[r.agent_name]["calls"] += 1

        for data in agents.values():
            data["total_tokens"] = data["input_tokens"] + data["output_tokens"]

        return agents

    def summary_table(self) -> str:
        """ASCII table for console output."""
        agents = self.by_agent()
        totals = self.total()

        if not self._records:
            return "(no token usage recorded)"

        # column widths
        rows = []
        for name, data in sorted(agents.items()):
            rows.append((
                name,
                str(data["input_tokens"]),
                str(data["output_tokens"]),
                str(data["total_tokens"]),
                str(data["calls"]),
            ))

        # totals row
        total_row = (
            "TOTAL",
            str(totals["input_tokens"]),
            str(totals["output_tokens"]),
            str(totals["total_tokens"]),
            str(totals["num_llm_calls"]),
        )

        headers = ("Agent", "Input", "Output", "Total", "Calls")

        # max of header and data cells
        all_rows = [headers] + rows + [total_row]
        widths = [max(len(row[i]) for row in all_rows) for i in range(5)]

        def fmt_row(cells):
            parts = []
            for i, cell in enumerate(cells):
                if i == 0:
                    parts.append(cell.ljust(widths[i]))
                else:
                    # right-align numbers
                    parts.append(cell.rjust(widths[i]))
            return "| " + " | ".join(parts) + " |"

        sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"

        lines = [
            sep,
            fmt_row(headers),
            sep,
        ]
        for row in rows:
            lines.append(fmt_row(row))
        lines.append(sep)
        lines.append(fmt_row(total_row))
        lines.append(sep)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """JSON-serializable export."""
        return {
            "total": self.total(),
            "by_agent": self.by_agent(),
            "raw_log": [
                {
                    "agent_name": r.agent_name,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "model": r.model,
                    "timestamp": r.timestamp,
                }
                for r in self._records
            ],
        }
