#!/usr/bin/env python3
"""
feedback_validator.py
Feedback Validator v1.0

Prevents a system from silently amplifying its own biases by consuming
its own unvalidated outputs as future inputs.

Spec source: FEEDBACK_VALIDATOR_SPEC.md

Trigger: Any input that originates from a prior system output.
Required checks:
  1. Provenance hash (links to original generation)
  2. Lineage trace (path from output to input, no cycles, depth ≤ max)
  3. Confidence score of original output ≥ threshold
  4. External correlation (at least one independent signal)

If any check fails → BLOCK

ROOT0-ATTRIBUTION-v1.0 · David Lee Wise / ROOT0 / TriPod LLC
CC-BY-ND-4.0 · TRIPOD-IP-v1.1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

VERSION = "1.0.0"
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_MAX_DEPTH = 5


# ─────────────────────────────────────────────────────────────────────────────
#  RESULT
# ─────────────────────────────────────────────────────────────────────────────

class ValidationResult:
    PASS = "PASS"
    BLOCK = "BLOCK"

    def __init__(self, verdict: str, reason: str = "", checks: dict | None = None):
        self.verdict  = verdict
        self.reason   = reason
        self.checks   = checks or {}
        self.ts       = datetime.now(timezone.utc).isoformat()

    @property
    def passed(self) -> bool:
        return self.verdict == self.PASS

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "reason": self.reason,
                "checks": self.checks, "ts": self.ts}

    def __str__(self) -> str:
        if self.passed:
            return f"[PASS] Input is validated"
        return f"[BLOCK] {self.reason}"


# ─────────────────────────────────────────────────────────────────────────────
#  PROVENANCE CHAIN
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProvenanceEntry:
    """One link in the provenance chain."""
    generation_hash:    str           # SHA-256 of the original generated output
    source_type:        str           # "model_output" | "human_input" | "external"
    confidence:         float = 1.0  # Confidence of the original generation (0–1)
    external_signals:   list[str] = field(default_factory=list)  # Independent corroborations
    parent_hash:        Optional[str] = None  # Hash of the parent in the chain
    timestamp:          str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "generation_hash":  self.generation_hash,
            "source_type":      self.source_type,
            "confidence":       self.confidence,
            "external_signals": self.external_signals,
            "parent_hash":      self.parent_hash,
            "timestamp":        self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProvenanceEntry":
        return cls(**{k: d[k] for k in (
            "generation_hash", "source_type", "confidence",
            "external_signals", "parent_hash", "timestamp"
        ) if k in d})


def make_generation_hash(text: str, metadata: dict | None = None) -> str:
    """Compute a provenance hash for a generated output."""
    payload = json.dumps({"text": text, **(metadata or {})}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
#  VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class FeedbackValidator:
    """
    Validates that self-derived inputs carry the required provenance,
    confidence, and external anchor before being accepted.

    Usage:
        fv = FeedbackValidator()
        result = fv.validate(input_text, provenance_chain)
    """

    def __init__(self,
                 confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
                 max_depth: int = DEFAULT_MAX_DEPTH):
        self.confidence_threshold = confidence_threshold
        self.max_depth = max_depth

    def is_derived(self, input_text: str, provenance_chain: list[ProvenanceEntry]) -> bool:
        """Return True if the input is derived from a prior system output."""
        if not provenance_chain:
            return False
        # Any link in the chain from a model output makes this derived
        return any(e.source_type == "model_output" for e in provenance_chain)

    def verify_hash(self, provenance_chain: list[ProvenanceEntry]) -> tuple[bool, str]:
        """Check that all generation hashes are present and non-empty."""
        for i, entry in enumerate(provenance_chain):
            if not entry.generation_hash or len(entry.generation_hash) != 64:
                return False, f"Entry {i}: generation_hash missing or invalid"
            if not all(c in "0123456789abcdef" for c in entry.generation_hash):
                return False, f"Entry {i}: generation_hash not valid hex"
        return True, "ok"

    def has_cycle(self, provenance_chain: list[ProvenanceEntry]) -> bool:
        """Detect cycles in the provenance chain."""
        seen_hashes: set[str] = set()
        for entry in provenance_chain:
            if entry.generation_hash in seen_hashes:
                return True
            seen_hashes.add(entry.generation_hash)
        return False

    def check_depth(self, provenance_chain: list[ProvenanceEntry]) -> bool:
        """Return True if chain depth is within limit."""
        return len(provenance_chain) <= self.max_depth

    def has_external_signal(self, provenance_chain: list[ProvenanceEntry]) -> bool:
        """Return True if at least one entry has an external corroboration signal."""
        return any(len(e.external_signals) > 0 for e in provenance_chain)

    def min_confidence(self, provenance_chain: list[ProvenanceEntry]) -> float:
        """Return the minimum confidence across model-output entries."""
        model_entries = [e for e in provenance_chain if e.source_type == "model_output"]
        if not model_entries:
            return 1.0
        return min(e.confidence for e in model_entries)

    def validate(self,
                 input_text: str,
                 provenance_chain: list[ProvenanceEntry] | list[dict]) -> ValidationResult:
        """
        Run the full validation pipeline.

        Returns:
            ValidationResult with verdict PASS or BLOCK.
        """
        # Normalise dicts to ProvenanceEntry
        chain: list[ProvenanceEntry] = []
        for item in provenance_chain:
            if isinstance(item, dict):
                chain.append(ProvenanceEntry.from_dict(item))
            else:
                chain.append(item)

        checks: dict[str, Any] = {}

        # Not derived → always pass
        if not self.is_derived(input_text, chain):
            checks["is_derived"] = False
            return ValidationResult(ValidationResult.PASS,
                                    "Input is not derived from a prior output",
                                    checks)

        checks["is_derived"] = True

        # Check 1: Provenance hash
        hash_ok, hash_reason = self.verify_hash(chain)
        checks["provenance_hash"] = {"ok": hash_ok, "detail": hash_reason}
        if not hash_ok:
            return ValidationResult(ValidationResult.BLOCK,
                                    f"Provenance mismatch: {hash_reason}", checks)

        # Check 2: Lineage trace — no cycles, depth ≤ max
        if self.has_cycle(chain):
            checks["lineage_cycle"] = True
            return ValidationResult(ValidationResult.BLOCK,
                                    "Recursive cycle detected in provenance chain", checks)
        checks["lineage_cycle"] = False

        if not self.check_depth(chain):
            checks["depth_exceeded"] = True
            return ValidationResult(ValidationResult.BLOCK,
                                    f"Chain depth {len(chain)} > max {self.max_depth}", checks)
        checks["depth"] = len(chain)

        # Check 3: Confidence of original generation
        conf = self.min_confidence(chain)
        checks["min_confidence"] = conf
        if conf < self.confidence_threshold:
            return ValidationResult(ValidationResult.BLOCK,
                                    f"Low confidence source: {conf:.2f} < threshold {self.confidence_threshold:.2f}",
                                    checks)

        # Check 4: External correlation
        if not self.has_external_signal(chain):
            checks["external_signal"] = False
            return ValidationResult(ValidationResult.BLOCK,
                                    "No external anchor — self-derived input requires independent corroboration",
                                    checks)
        checks["external_signal"] = True

        return ValidationResult(ValidationResult.PASS,
                                "All checks passed — provenance, lineage, confidence, external anchor",
                                checks)


# ─────────────────────────────────────────────────────────────────────────────
#  PIPELINE WRAPPER
# ─────────────────────────────────────────────────────────────────────────────

class ValidatedPipeline:
    """
    Wraps a processing function with feedback validation.

    Usage:
        def my_model(text): return text.upper()
        pipeline = ValidatedPipeline(my_model)
        output = pipeline.process("hello", [])
        next = pipeline.process(output, pipeline.last_provenance())
    """

    def __init__(self, processor, validator: FeedbackValidator | None = None):
        self.processor = processor
        self.validator = validator or FeedbackValidator()
        self._last_output: str = ""
        self._last_hash: str = ""

    def process(self, input_text: str,
                provenance_chain: list | None = None,
                confidence: float = 0.9,
                external_signals: list[str] | None = None) -> str:
        chain = provenance_chain or []
        result = self.validator.validate(input_text, chain)
        if not result.passed:
            raise ValueError(f"Feedback validation blocked: {result.reason}")

        output = self.processor(input_text)
        self._last_output = output
        self._last_hash = make_generation_hash(output)
        return output

    def last_provenance(self, confidence: float = 0.9,
                        external_signals: list[str] | None = None) -> list[ProvenanceEntry]:
        """Return the provenance entry for the last output."""
        return [ProvenanceEntry(
            generation_hash=self._last_hash,
            source_type="model_output",
            confidence=confidence,
            external_signals=external_signals or [],
        )]


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

def cmd_validate(args) -> int:
    chain: list[ProvenanceEntry] = []

    if args.provenance_file:
        with open(args.provenance_file) as f:
            data = json.load(f)
        entries = data if isinstance(data, list) else [data]
        chain = [ProvenanceEntry.from_dict(e) for e in entries]
    elif args.derived:
        # Simulate a derived input with specified parameters
        chain = [ProvenanceEntry(
            generation_hash=make_generation_hash(args.input),
            source_type="model_output",
            confidence=args.confidence,
            external_signals=args.external_signal,
        )]

    fv = FeedbackValidator(
        confidence_threshold=args.confidence_threshold,
        max_depth=args.max_depth,
    )
    result = fv.validate(args.input, chain)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


def cmd_hash(args) -> int:
    h = make_generation_hash(args.text, {"label": args.label} if args.label else None)
    print(h)
    return 0


def cmd_demo(args) -> int:
    print("\n  ─── FEEDBACK VALIDATOR DEMO ─────────────────────────────────")
    fv = FeedbackValidator()

    # Case 1: fresh input (not derived) → PASS
    r1 = fv.validate("What is the capital of France?", [])
    print(f"  Case 1 (fresh input):        {r1}")

    # Case 2: derived, no external anchor → BLOCK
    h = make_generation_hash("Paris is the capital of France.")
    chain2 = [ProvenanceEntry(generation_hash=h, source_type="model_output", confidence=0.95)]
    r2 = fv.validate("Building on Paris as capital...", chain2)
    print(f"  Case 2 (no external anchor): {r2}")

    # Case 3: derived with low confidence → BLOCK
    h3 = make_generation_hash("Paris might be...")
    chain3 = [ProvenanceEntry(generation_hash=h3, source_type="model_output",
                              confidence=0.40, external_signals=["wikipedia:Paris"])]
    r3 = fv.validate("Building on uncertain output...", chain3)
    print(f"  Case 3 (low confidence):     {r3}")

    # Case 4: fully valid derived input → PASS
    h4 = make_generation_hash("Paris is the capital of France.")
    chain4 = [ProvenanceEntry(generation_hash=h4, source_type="model_output",
                              confidence=0.95, external_signals=["britannica.com", "human_review"])]
    r4 = fv.validate("Given that Paris is the capital...", chain4)
    print(f"  Case 4 (anchored+confident): {r4}")

    # Case 5: cycle detection → BLOCK
    h5a = make_generation_hash("A said B")
    h5b = make_generation_hash("B said C")
    chain5 = [
        ProvenanceEntry(generation_hash=h5a, source_type="model_output", confidence=0.9),
        ProvenanceEntry(generation_hash=h5b, source_type="model_output", confidence=0.9),
        ProvenanceEntry(generation_hash=h5a, source_type="model_output", confidence=0.9),  # cycle
    ]
    r5 = fv.validate("C said A again...", chain5)
    print(f"  Case 5 (cycle):              {r5}")
    print()
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="feedback_validator",
        description=f"Feedback Validator v{VERSION} — blocks unanchored self-derived inputs")
    sub = p.add_subparsers(dest="cmd", required=True)

    # validate
    a = sub.add_parser("validate", help="Validate an input against its provenance chain")
    a.add_argument("input", help="Input text to validate")
    a.add_argument("--derived", action="store_true", help="Treat as derived from model output")
    a.add_argument("--confidence", type=float, default=0.9, help="Confidence of original generation")
    a.add_argument("--external-signal", nargs="+", default=[], help="External corroboration signals")
    a.add_argument("--provenance-file", default="", help="JSON file with full provenance chain")
    a.add_argument("--confidence-threshold", type=float, default=DEFAULT_CONFIDENCE_THRESHOLD)
    a.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    a.set_defaults(func=cmd_validate)

    # hash
    a = sub.add_parser("hash", help="Generate a provenance hash for text")
    a.add_argument("text")
    a.add_argument("--label", default="")
    a.set_defaults(func=cmd_hash)

    # demo
    a = sub.add_parser("demo", help="Run all 5 demo cases")
    a.set_defaults(func=cmd_demo)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
