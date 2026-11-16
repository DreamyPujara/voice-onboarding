# Voice Onboarding Funnel Simulator

A tiny offline CLI for a product experimenter comparing **synthetic** voice-first onboarding flows before collecting real evidence.

## User problem

When sketching onboarding flows, it is easy to mix invalid funnel events with optimistic assumptions. This tool validates event order and reports simple completion/dropoff summaries while keeping assumptions editable in JSON.

## Run

```bash
python tool.py
python tool.py examples/demo.json --json
python -m unittest discover
```

## Input shape

JSON contains `assumptions` and `events`. Each event needs `participant`, `flow`, `event`, and ISO `ts`. Supported events are `start`, `complete`, and `dropoff` by default. Malformed objects, empty event lists, invalid assumptions, missing fields, and unsupported event names return explicit validation errors.

## Metrics

Per flow the CLI reports:

- starts, completes, dropoffs
- completion and dropoff rates
- median time-to-completion in minutes

Invalid inputs return exit code `2` and list validation errors. Naive ISO timestamps are treated as UTC so old fixture files remain usable; include `Z` or an offset for clarity.

## Tradeoffs and non-goals

This first version is intentionally small: no network calls, no personal data, no persistence, no charts, no statistics beyond descriptive funnel metrics, and no claim that synthetic results predict real conversion.

AI assistance was used to draft this code and documentation. Review assumptions and validation rules before relying on outputs.
