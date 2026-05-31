#!/bin/bash
# log_voltage.sh — one-liner wrapper for event_anchor_logger.py
# Usage: ./log_voltage.sh <voltage_mv> <bit_index> [description] [output_file]
VOLTAGE="${1:--211}"
BIT="${2:-65}"
DESC="${3:-Gate threshold measurement}"
OUT="${4:-voltage_anchor_$(date -u +%Y%m%dT%H%M%SZ).md}"
python3 "$(dirname "$0")/event_anchor_logger.py" \
  --voltage "$VOLTAGE" --bit "$BIT" --description "$DESC" --output "$OUT"
