#!/usr/bin/env python3
"""
event_anchor_logger.py

Stable, grounded anchor logger.

Purpose:
- record a timestamped event
- attach index / polarity / value / description
- write a deterministic markdown record
- compute SHA256 over the canonical payload

This script does NOT claim hardware success, bit flips, or state changes.
It only records a structured event.

Example:
    python3 event_anchor_logger.py \
      --value +211 \
      --index 65 \
      --label "Forward pulse threshold" \
      --output forward_anchor.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AnchorEvent:
    timestamp_utc: str
    index: int
    value: str
    label: str
    event_type: str
    notes: str = ""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_payload(event: AnchorEvent) -> str:
    """
    Deterministic JSON string used for hashing.
    """
    return json.dumps(
        asdict(event),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def markdown_record(event: AnchorEvent, digest: str) -> str:
    lines = [
        "# Anchor Event",
        "",
        f"- **Timestamp (UTC):** `{event.timestamp_utc}`",
        f"- **Event Type:** `{event.event_type}`",
        f"- **Index:** `{event.index}`",
        f"- **Value:** `{event.value}`",
        f"- **Label:** {event.label}",
    ]
    if event.notes.strip():
        lines.append(f"- **Notes:** {event.notes.strip()}")
    lines.extend(
        [
            f"- **SHA256:** `{digest}`",
            "",
            "## Canonical Payload",
            "",
            "```json",
            json.dumps(asdict(event), ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a deterministic markdown anchor record."
    )
    parser.add_argument(
        "--value",
        required=True,
        help='Recorded value, e.g. +211, -211, 0.35, "forward".',
    )
    parser.add_argument(
        "--index",
        required=True,
        type=int,
        help="Indexed location for the event.",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Human-readable event label.",
    )
    parser.add_argument(
        "--event-type",
        default="threshold_probe",
        help="Structured event type. Default: threshold_probe",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output markdown file path.",
    )
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.index < 0:
        raise ValueError("--index must be >= 0")
    if not args.label.strip():
        raise ValueError("--label must not be empty")
    if not args.output.strip():
        raise ValueError("--output must not be empty")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        validate_args(args)

        event = AnchorEvent(
            timestamp_utc=utc_now_iso(),
            index=args.index,
            value=str(args.value),
            label=args.label.strip(),
            event_type=args.event_type.strip() or "threshold_probe",
            notes=args.notes.strip(),
        )

        payload = canonical_payload(event)
        digest = sha256_hex(payload)
        record = markdown_record(event, digest)

        out_path = Path(args.output)
        write_text(out_path, record)

        print(f"Wrote anchor record: {out_path}")
        print(f"SHA256: {digest}")
        return 0

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
