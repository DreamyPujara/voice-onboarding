#!/usr/bin/env python3
"""Offline simulator for synthetic voice-onboarding funnel events."""
import argparse, json, statistics, sys
from datetime import datetime, timezone

DEFAULT_DATA = {
    "assumptions": {
        "description": "Synthetic demo only; not user research.",
        "flows": ["guided", "fast"],
        "terminal_events": ["complete", "dropoff"]
    },
    "events": [
        {"participant":"p1","flow":"guided","event":"start","ts":"2026-01-01T09:00:00Z"},
        {"participant":"p1","flow":"guided","event":"complete","ts":"2026-01-01T09:04:30Z"},
        {"participant":"p2","flow":"guided","event":"start","ts":"2026-01-01T09:01:00Z"},
        {"participant":"p2","flow":"guided","event":"dropoff","ts":"2026-01-01T09:03:00Z"},
        {"participant":"p3","flow":"fast","event":"start","ts":"2026-01-01T09:02:00Z"},
        {"participant":"p3","flow":"fast","event":"complete","ts":"2026-01-01T09:03:15Z"}
    ]
}

REQUIRED = {"participant", "flow", "event", "ts"}


def parse_ts(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_data(path):
    if not path:
        return DEFAULT_DATA
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(data):
    if not isinstance(data, dict):
        return ["input must be a JSON object with assumptions and events"]
    assumptions = data.get("assumptions", {})
    if assumptions is None:
        assumptions = {}
    if not isinstance(assumptions, dict):
        return ["assumptions must be an object"]
    flows_raw = assumptions.get("flows", [])
    terminals_raw = assumptions.get("terminal_events", ["complete", "dropoff"])
    errors = []
    if not isinstance(flows_raw, list) or any(not isinstance(f, str) or not f for f in flows_raw):
        errors.append("assumptions.flows must be a list of non-empty strings")
        flows = set()
    else:
        flows = set(flows_raw)
    if not isinstance(terminals_raw, list) or any(not isinstance(t, str) or not t for t in terminals_raw):
        errors.append("assumptions.terminal_events must be a list of non-empty strings")
        terminals = {"complete", "dropoff"}
    else:
        terminals = set(terminals_raw)
    events = data.get("events")
    if not isinstance(events, list):
        return errors + ["events must be a list"]
    if not events:
        return errors + ["events must contain at least one event"]
    by_person = {}
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            errors.append(f"event {i} must be an object")
            continue
        missing = REQUIRED - set(ev)
        if missing:
            errors.append(f"event {i} missing {', '.join(sorted(missing))}")
            continue
        for field in ("participant", "flow", "event"):
            if not isinstance(ev[field], str) or not ev[field]:
                errors.append(f"event {i} field {field} must be a non-empty string")
        if flows and ev["flow"] not in flows:
            errors.append(f"event {i} has unknown flow {ev['flow']!r}")
        if ev["event"] not in ({"start"} | terminals):
            errors.append(f"event {i} has unsupported event {ev['event']!r}")
        try:
            ts = parse_ts(ev["ts"])
        except ValueError as exc:
            errors.append(f"event {i} {exc}")
            continue
        if all(isinstance(ev[f], str) and ev[f] for f in ("participant", "flow", "event")):
            by_person.setdefault((ev["participant"], ev["flow"]), []).append((ts, i, ev["event"]))
    for key, rows in by_person.items():
        rows.sort(key=lambda row: (row[0], row[1]))
        seen_start = False
        terminal_count = 0
        for ts, idx, name in rows:
            if name == "start":
                if seen_start:
                    errors.append(f"event {idx} repeats start for {key[0]} in {key[1]}")
                seen_start = True
            elif name in terminals:
                terminal_count += 1
                if not seen_start:
                    errors.append(f"event {idx} has terminal before start for {key[0]} in {key[1]}")
        if terminal_count > 1:
            errors.append(f"{key[0]} in {key[1]} has multiple terminal events")
    return errors


def summarize(data):
    errors = validate(data)
    if errors:
        return {"valid": False, "errors": errors}
    flows = data.get("assumptions", {}).get("flows") or sorted({e["flow"] for e in data["events"]})
    rows = {f: {"starts": 0, "completes": 0, "dropoffs": 0, "durations": []} for f in flows}
    starts = {}
    for ev in sorted(data["events"], key=lambda e: parse_ts(e["ts"])):
        key = (ev["participant"], ev["flow"])
        bucket = rows.setdefault(ev["flow"], {"starts":0,"completes":0,"dropoffs":0,"durations":[]})
        if ev["event"] == "start":
            bucket["starts"] += 1
            starts[key] = parse_ts(ev["ts"])
        elif ev["event"] == "complete":
            bucket["completes"] += 1
            bucket["durations"].append((parse_ts(ev["ts"]) - starts[key]).total_seconds() / 60)
        elif ev["event"] == "dropoff":
            bucket["dropoffs"] += 1
    for f, b in rows.items():
        s = b["starts"] or 1
        b["completion_rate"] = round(b["completes"] / s, 3)
        b["dropoff_rate"] = round(b["dropoffs"] / s, 3)
        b["median_completion_minutes"] = None if not b["durations"] else round(statistics.median(b.pop("durations")), 2)
    return {"valid": True, "assumptions": data.get("assumptions", {}), "flows": rows}


def text_report(result):
    if not result["valid"]:
        return "Invalid funnel events:\n- " + "\n- ".join(result["errors"])
    lines = ["Voice onboarding synthetic funnel summary", "Assumptions: " + result["assumptions"].get("description", "not provided")]
    for flow, b in result["flows"].items():
        lines.append(f"{flow}: starts={b['starts']} completes={b['completes']} dropoffs={b['dropoffs']} completion={b['completion_rate']:.1%} median_minutes={b['median_completion_minutes']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and summarize synthetic voice onboarding events.")
    parser.add_argument("input", nargs="?", help="JSON file; omitted uses built-in synthetic demo")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)
    result = summarize(load_data(args.input))
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else text_report(result))
    return 0 if result["valid"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
