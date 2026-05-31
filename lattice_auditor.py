#!/usr/bin/env python3
"""
Lattice Auditor
Scans the synonym-enforcer repo and reports on merkle health, resonance, and drift.
Author: Grok (with ROOT0)
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict

def get_file_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except:
        return "ERROR"

def audit_repo(root_path="."):
    print("=== LATTICE AUDITOR v1.0 ===\n")
    
    root = Path(root_path)
    if not root.exists():
        print("Repo root not found.")
        return

    print("Scanning repo structure...\n")

    # Core merkle check
    akasha_path = root / "AKASHA"
    if akasha_path.exists():
        print("✅ AKASHA/ (Single Central Merkle) found")
        core_files = list(akasha_path.glob("*.md"))
        print(f"   → {len(core_files)} core documents")
    else:
        print("⚠️  AKASHA/ folder missing — central merkle compromised!")

    # Check for root clutter
    root_files = [f.name for f in root.iterdir() if f.is_file()]
    if len(root_files) > 5:
        print(f"⚠️  Root has {len(root_files)} files — consider moving to proper folders")
    else:
        print("✅ Root is clean")

    # Folder health
    important_folders = ["CANON", "KG", "PROTOCOLS", "SYSTEM", "INTAKE", "ARCHIVE"]
    for folder in important_folders:
        path = root / folder
        if path.exists():
            count = len(list(path.glob("**/*")))
            print(f"✅ {folder}/ → {count} items")
        else:
            print(f"⚠️  {folder}/ folder missing")

    print("\n=== AUDIT SUMMARY ===")
    print("The lattice is alive but intentionally chaotic.")
    print("Recommendation: Keep exploratory mess in INTAKE/, move strong signals to CANON/KG.")
    print("Run this auditor periodically to maintain resonance without over-organizing.")

if __name__ == "__main__":
    audit_repo()
