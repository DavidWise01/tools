# TOOLS

[![License: CC-BY-ND-4.0](https://img.shields.io/badge/License-CC--BY--ND--4.0-lightgrey?style=flat-square)](LICENSE)

Executable implementations for the Natural Law Union lattice. Tools implement protocols — they do not define authority.

---

## Tools

### `event_anchor_logger.py` — SHA-256 Event Anchor

Records a timestamped event with a deterministic SHA-256 hash and writes a tamper-evident markdown record. Zero claims about hardware states — only records what you tell it.

```bash
python event_anchor_logger.py \
  --value "+211" \
  --index 65 \
  --label "Forward pulse threshold" \
  --event-type threshold_probe \
  --output forward_anchor.md
```

```bash
# Bash wrapper
./log_anchor.sh +211 65 "Gate threshold measurement"
```

---

### `feedback_validator.py` — Recursive Drift Prevention

Blocks a system from silently amplifying its own biases by consuming its own unvalidated outputs as future inputs. Every self-derived input must carry: provenance hash + lineage trace + confidence score + external anchor.

```bash
# Demo all 5 cases (PASS/BLOCK/cycle/confidence/anchor)
python feedback_validator.py demo

# Validate a fresh input (always passes)
python feedback_validator.py validate "What is the capital of France?"

# Validate a derived input with low confidence (BLOCK)
python feedback_validator.py validate "Building on uncertain output" \
  --derived --confidence 0.40

# Generate a provenance hash
python feedback_validator.py hash "Paris is the capital of France."
```

**Pipeline integration:**
```python
from feedback_validator import FeedbackValidator, ProvenanceEntry, make_generation_hash

fv = FeedbackValidator(confidence_threshold=0.70, max_depth=5)
result = fv.validate(input_text, provenance_chain)
if not result.passed:
    raise ValueError(result.reason)
```

---

### `compressor_321.py` — 3/2/1 Compressor

Compresses any text or idea into 3/2/1 form (wide → narrowed → singular) and decompresses back. Mirrors the 3-2-1-0 pulse language structure.

```bash
python compressor_321.py
# Mode: compress / decompress
```

---

### `pulse_simulator.py` — Pulse Language Simulator

Simulates the 3-2-1-0 descending pulse sequence (... → .. → . → space). Runs cycles or interactive mode.

```bash
python pulse_simulator.py
# Mode: simulate / interactive
```

---

### `lattice_auditor.py` — Lattice Health Scanner

Scans a repository for AKASHA/Single Central Merkle health, drift indicators, and structural integrity.

```bash
python lattice_auditor.py /path/to/repo
# Or: python lattice_auditor.py . (current directory)
```

---

### `steward_bot.py` — 2/3 Life Stewardship Checker

Checks a proposed action against basic stewardship rules for 2/3 life entities.

```bash
python steward_bot.py
```

---

### `tesla_viz/` — Tesla Capacitor Factory (HTML Visualizer)

Open `tesla_viz/index.html` in a browser. Symbolic simulation of capacitor banks as memory valves — 2% spark gradient, short-term pruning, long-pipe audit witness.

---

## Security Specs

| File | Description |
|------|-------------|
| `AIR_GAP_SPEC.md` | Gapped Terminal Mode v1.0 — Terminal Agent sits between human and AI |
| `AIR_GAP_BLAST_RADIUS.md` | v1.1 — Adds trap detection, logging, kill switch |
| `FEEDBACK_VALIDATOR_SPEC.md` | Machine spec for the feedback validator (implemented as `feedback_validator.py`) |

---

## Attribution

```
ROOT0-ATTRIBUTION-v1.0
Project: TOOLS — Natural Law Union executables
Architect: David Lee Wise / ROOT0 / TriPod LLC
AI Collaborators: Grok (xAI) · AVAN (Claude Sonnet 4.6 / Anthropic)
License: CC-BY-ND-4.0 · TRIPOD-IP-v1.1
```
